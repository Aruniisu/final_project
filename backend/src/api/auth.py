"""Auth API — Premium single-user auth + settings + OAuth + audit logs"""
from flask import Blueprint, request, jsonify, make_response, redirect
from datetime import datetime
import os
import time
import secrets
from collections import defaultdict
import requests

from database.managers.user_manager import UserManager
from database.connection import db_connection

auth_bp = Blueprint('auth', __name__)

# ═══════════════════════════════════════════════════════════
# RATE LIMIT
# ═══════════════════════════════════════════════════════════
_login_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = 900
RATE_LIMIT_MAX = 5

# ═══════════════════════════════════════════════════════════
# OAUTH STATE
# ═══════════════════════════════════════════════════════════
_oauth_states = {}
OAUTH_STATE_TTL = 600


def _cleanup_states():
    now = time.time()
    expired = [s for s, t in _oauth_states.items() if now - t > OAUTH_STATE_TTL]
    for s in expired:
        _oauth_states.pop(s, None)


def _create_state():
    _cleanup_states()
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()
    return state


def _verify_state(state):
    _cleanup_states()
    if state in _oauth_states:
        _oauth_states.pop(state, None)
        return True
    return False


def check_rate_limit(ip):
    now = time.time()
    attempts = _login_attempts[ip]
    attempts[:] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    if len(attempts) >= RATE_LIMIT_MAX:
        return False, len(attempts)
    return True, len(attempts)


def record_attempt(ip):
    _login_attempts[ip].append(time.time())


def clear_attempts(ip):
    _login_attempts[ip] = []


def get_user_manager():
    return UserManager(db_connection.get_db())


def get_token_from_request():
    token = request.cookies.get('access_token')
    if not token:
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ')[1]
    return token


def _set_auth_cookies(response, access_token, refresh_token):
    secure = os.getenv('FLASK_ENV') == 'production'
    response.set_cookie('access_token', access_token, httponly=True, secure=secure,
                        samesite='Lax', max_age=900, path='/')
    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=secure,
                        samesite='Lax', max_age=604800, path='/')


def _mask_token(t):
    if not t:
        return None
    if len(t) < 8:
        return '****'
    return f"{t[:4]}****{t[-4:]}"


def _user_public(user):
    return {
        'id': user['user_id'],
        'name': user.get('name'),
        'email': user.get('email'),
        'role': user.get('role'),
    }


def _log_audit(user_id, action, target='', status='success', details='', ip=None):
    try:
        db = db_connection.get_db()
        db.audit_logs.insert_one({
            'user_id': user_id,
            'action': action,
            'target': target,
            'status': status,
            'details': details,
            'ip': ip or request.remote_addr or 'unknown',
            'timestamp': datetime.now(),
        })
    except Exception as e:
        print(f"[AUDIT] Failed: {e}")


def _redirect_to_frontend(path='/dashboard', query=''):
    frontend = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    url = f"{frontend}{path}"
    if query:
        url += f"?{query}"
    return redirect(url)


# ═══════════════════════════════════════════════════════════
# SETUP STATUS
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/setup-status', methods=['GET', 'OPTIONS'])
def setup_status():
    if request.method == 'OPTIONS':
        return '', 204
    um = get_user_manager()
    count = um.count_users()
    return jsonify({'needs_setup': count == 0, 'user_count': count})


# ═══════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/setup', methods=['POST', 'OPTIONS'])
def setup():
    if request.method == 'OPTIONS':
        return '', 204
    um = get_user_manager()
    if um.count_users() > 0:
        return jsonify({'error': 'System already initialized'}), 400

    data = request.json or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password required'}), 400
    if len(password) < 12:
        return jsonify({'error': 'Password must be at least 12 characters'}), 400
    if '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400

    user, error = um.create_user(name, email, password, role='admin')
    if error:
        return jsonify({'error': error}), 400

    session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
    access = um.generate_token(user['user_id'], session_minutes)
    refresh = um.generate_refresh_token(user['user_id'])
    um.update_last_login(user['user_id'])

    db = db_connection.get_db()
    db.users.update_one(
        {'user_id': user['user_id']},
        {'$set': {'password_changed_at': datetime.now()}}
    )

    _log_audit(user['user_id'], 'setup', target='system', status='success',
               details=f'Account created: {email}')

    resp = make_response(jsonify({
        'success': True,
        'message': 'Setup complete',
        'user': _user_public(user),
    }))
    _set_auth_cookies(resp, access, refresh)
    return resp


# ═══════════════════════════════════════════════════════════
# REGISTER (available anytime)
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    ip = request.remote_addr or 'unknown'
    allowed, count = check_rate_limit(ip)
    if not allowed:
        return jsonify({'error': 'Too many attempts. Try again in 15 minutes.'}), 429

    data = request.json or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not name or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    if len(password) < 12:
        return jsonify({'error': 'Password must be at least 12 characters'}), 400
    if '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400

    um = get_user_manager()
    is_first_user = um.count_users() == 0
    role = 'admin' if is_first_user else 'user'

    user, error = um.create_user(name, email, password, role=role)
    if error:
        record_attempt(ip)
        return jsonify({'error': error}), 400

    clear_attempts(ip)
    session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
    access = um.generate_token(user['user_id'], session_minutes)
    refresh = um.generate_refresh_token(user['user_id'])
    um.update_last_login(user['user_id'])

    db = db_connection.get_db()
    db.users.update_one(
        {'user_id': user['user_id']},
        {'$set': {'password_changed_at': datetime.now()}}
    )

    _log_audit(user['user_id'], 'register', target='account', status='success',
               details=f'New account: {email} ({role})', ip=ip)

    resp = make_response(jsonify({
        'success': True,
        'message': 'Account created',
        'user': _user_public(user),
        'is_first_user': is_first_user,
    }))
    _set_auth_cookies(resp, access, refresh)
    return resp


# ═══════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    ip = request.remote_addr or 'unknown'
    allowed, count = check_rate_limit(ip)
    if not allowed:
        return jsonify({'error': 'Too many attempts. Try again in 15 minutes.'}), 429

    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    um = get_user_manager()
    user = um.find_by_email(email)
    if not user or not um.verify_password(user, password):
        record_attempt(ip)
        if user:
            _log_audit(user['user_id'], 'login', target='system', status='failed',
                       details='Invalid password', ip=ip)
        remaining = RATE_LIMIT_MAX - count - 1
        return jsonify({'error': 'Invalid credentials', 'attempts_remaining': max(0, remaining)}), 401

    clear_attempts(ip)
    um.update_last_login(user['user_id'])
    _log_audit(user['user_id'], 'login', target='system', status='success',
               details='Email/password login', ip=ip)

    session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
    access = um.generate_token(user['user_id'], session_minutes)
    refresh = um.generate_refresh_token(user['user_id'])

    resp = make_response(jsonify({
        'success': True,
        'message': 'Login successful',
        'user': _user_public(user),
    }))
    _set_auth_cookies(resp, access, refresh)
    return resp


# ═══════════════════════════════════════════════════════════
# REFRESH / ME / LOGOUT
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/refresh', methods=['POST', 'OPTIONS'])
def refresh():
    if request.method == 'OPTIONS':
        return '', 204
    token = request.cookies.get('refresh_token')
    if not token:
        return jsonify({'error': 'No refresh token'}), 401

    um = get_user_manager()
    user_id = um.verify_token(token, token_type='refresh')
    if not user_id:
        return jsonify({'error': 'Invalid refresh token'}), 401

    user = um.find_by_user_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
    new_access = um.generate_token(user_id, session_minutes)
    resp = make_response(jsonify({'success': True, 'user': _user_public(user)}))
    resp.set_cookie('access_token', new_access, httponly=True,
                    samesite='Lax', max_age=session_minutes * 60, path='/')
    return resp


@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
def me():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401

    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    user = um.find_by_user_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    password_age_days = None
    password_expired = False
    if user.get('password_changed_at'):
        delta = datetime.now() - user['password_changed_at']
        password_age_days = delta.days
        expiry = user.get('settings', {}).get('passwordExpiry', 90)
        if password_age_days >= expiry:
            password_expired = True

    return jsonify({
        **_user_public(user),
        'profile': user.get('profile', {}),
        'tokens': {k: _mask_token(v) for k, v in (user.get('tokens') or {}).items()},
        'settings': user.get('settings', {}),
        'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
        'last_login': user['last_login'].isoformat() if user.get('last_login') else None,
        'password_age_days': password_age_days,
        'password_expired': password_expired,
    }), 200


@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if token:
        um = get_user_manager()
        user_id = um.verify_token(token)
        if user_id:
            _log_audit(user_id, 'logout', target='system', status='success',
                       details='User logged out')

    resp = make_response(jsonify({'success': True, 'message': 'Logged out'}))
    resp.delete_cookie('access_token', path='/')
    resp.delete_cookie('refresh_token', path='/')
    return resp


@auth_bp.route('/change-password', methods=['POST', 'OPTIONS'])
def change_password():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401

    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    current = data.get('current_password')
    new_pass = data.get('new_password')

    if not current or not new_pass:
        return jsonify({'error': 'Current and new password required'}), 400
    if len(new_pass) < 12:
        return jsonify({'error': 'New password must be at least 12 characters'}), 400

    user = um.find_by_user_id(user_id)
    if not um.verify_password(user, current):
        _log_audit(user_id, 'change_password', target='security', status='failed',
                   details='Wrong current password')
        return jsonify({'error': 'Current password is incorrect'}), 401

    if um.change_password(user_id, new_pass):
        db = db_connection.get_db()
        db.users.update_one(
            {'user_id': user_id},
            {'$set': {'password_changed_at': datetime.now()}}
        )
        _log_audit(user_id, 'change_password', target='security', status='success',
                   details='Password updated')
        return jsonify({'success': True, 'message': 'Password changed'}), 200
    return jsonify({'error': 'Failed to change password'}), 500


@auth_bp.route('/update-profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401

    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    if um.update_profile(user_id, data):
        _log_audit(user_id, 'update_profile', target='account', status='success',
                   details='Profile updated')
        return jsonify({'success': True, 'message': 'Profile updated'}), 200
    return jsonify({'error': 'Failed to update'}), 500


# ═══════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/settings', methods=['GET', 'OPTIONS'])
def get_settings():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    user = um.find_by_user_id(user_id)
    return jsonify({'success': True, 'settings': user.get('settings', {})})


@auth_bp.route('/settings', methods=['PUT', 'OPTIONS'])
def update_settings():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    if um.update_settings(user_id, data):
        _log_audit(user_id, 'settings_update', target='settings', status='success',
                   details=f'Updated {len(data)} keys')
        return jsonify({'success': True, 'message': 'Settings updated'}), 200
    return jsonify({'error': 'Failed'}), 500


@auth_bp.route('/tokens', methods=['PUT', 'OPTIONS'])
def update_tokens():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    if um.update_tokens(user_id, data):
        return jsonify({'success': True, 'message': 'Tokens updated'}), 200
    return jsonify({'error': 'Failed'}), 500


@auth_bp.route('/verify-github', methods=['POST', 'OPTIONS'])
def verify_github():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    github_token = (data.get('github_token') or '').strip()
    if not github_token:
        return jsonify({'error': 'GitHub token required'}), 400

    try:
        r = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {github_token}'},
            timeout=10,
        )
        if r.status_code == 200:
            gh = r.json()
            um.update_tokens(user_id, {'github': github_token})
            _log_audit(user_id, 'github_connect', target='integration', status='success',
                       details=f'Connected as {gh.get("login")}')
            return jsonify({
                'success': True, 'valid': True,
                'user': {
                    'login': gh.get('login'),
                    'name': gh.get('name'),
                    'avatar': gh.get('avatar_url'),
                },
            }), 200
        else:
            return jsonify({
                'success': False, 'valid': False,
                'error': f'GitHub API returned {r.status_code}',
            }), 400
    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


@auth_bp.route('/tokens/<service>', methods=['DELETE', 'OPTIONS'])
def disconnect_token(service):
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    db = db_connection.get_db()
    db.users.update_one(
        {'user_id': user_id},
        {'$unset': {f'tokens.{service}': ''}}
    )
    _log_audit(user_id, f'{service}_disconnect', target='integration', status='success',
               details=f'{service} disconnected')
    return jsonify({'success': True, 'message': f'{service} disconnected'}), 200


# ═══════════════════════════════════════════════════════════
# AUDIT LOGS
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/audit-logs', methods=['GET', 'OPTIONS'])
def get_audit_logs():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401

    limit = int(request.args.get('limit', 100))

    try:
        db = db_connection.get_db()
        cursor = db.audit_logs.find({'user_id': user_id}).sort('timestamp', -1).limit(limit)

        logs = []
        for doc in cursor:
            ts = doc.get('timestamp')
            logs.append({
                'id': str(doc.get('_id', '')),
                'user': user_id[:8] + '...',
                'action': doc.get('action', 'unknown'),
                'target': doc.get('target', ''),
                'status': doc.get('status', 'success'),
                'details': doc.get('details', ''),
                'ip': doc.get('ip', ''),
                'time': ts.strftime('%Y-%m-%d %H:%M:%S') if ts else '',
                'timestamp': ts.isoformat() if ts else None,
            })

        return jsonify({'success': True, 'logs': logs}), 200
    except Exception as e:
        print(f"[AUDIT] Fetch error: {e}")
        return jsonify({'success': False, 'error': str(e), 'logs': []}), 500


# ═══════════════════════════════════════════════════════════
# ⭐ TEST EMAIL (single endpoint — no duplicates)
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/test-email', methods=['POST', 'OPTIONS'])
def test_email():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    user = um.find_by_user_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        from services.email_service import email_service
        if not email_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'SMTP not configured. Add SMTP_USER + SMTP_PASSWORD to .env',
            }), 400

        subject = "✅ Test Email from Smart DevOps"
        body = (f"Hello {user.get('name', 'there')}!\n\n"
                f"This is a test email from your Smart DevOps Assistant.\n\n"
                f"If you received this, your email notifications are working correctly.\n\n"
                f"Account: {user.get('email')}\n"
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        success, err = email_service.send(user['email'], subject, body)

        if success:
            _log_audit(user_id, 'test_email', target='notification',
                       status='success', details=f'To {user["email"]}')
            return jsonify({'success': True, 'message': f'Email sent to {user["email"]}'}), 200
        return jsonify({'success': False, 'error': err}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════
# TEST SLACK
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/test-slack', methods=['POST', 'OPTIONS'])
def test_slack():
    if request.method == 'OPTIONS':
        return '', 204
    token = get_token_from_request()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    um = get_user_manager()
    user_id = um.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    user = um.find_by_user_id(user_id)
    webhook = (user.get('tokens') or {}).get('slack_webhook')
    if not webhook:
        return jsonify({
            'success': False,
            'error': 'No Slack webhook configured. Add it first.',
        }), 400

    try:
        r = requests.post(
            webhook,
            json={'text': '✅ *Test message from Smart DevOps*\n\nYour Slack integration is working!'},
            timeout=10,
        )
        if r.status_code == 200:
            _log_audit(user_id, 'test_slack', target='notification', status='success',
                       details='Test message sent')
            return jsonify({'success': True, 'message': 'Test message sent to Slack'}), 200
        return jsonify({'success': False, 'error': f'Slack returned {r.status_code}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════
# 🌐 OAUTH — REDIRECT FLOW
# ═══════════════════════════════════════════════════════════
@auth_bp.route('/oauth/status', methods=['GET', 'OPTIONS'])
def oauth_status():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({
        'github': bool(os.getenv('GITHUB_CLIENT_ID') and os.getenv('GITHUB_CLIENT_SECRET')),
        'google': bool(os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET')),
    })


# ─── GitHub OAuth ───
@auth_bp.route('/oauth/github/start', methods=['GET'])
def oauth_github_start():
    client_id = os.getenv('GITHUB_CLIENT_ID')
    if not client_id:
        return _redirect_to_frontend('/login', 'error=oauth_not_configured')

    state = _create_state()
    backend = os.getenv('BACKEND_URL', 'http://localhost:5000')

    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={backend}/api/auth/oauth/github/callback"
        f"&scope=read:user%20user:email"
        f"&state={state}"
    )
    return redirect(url)


@auth_bp.route('/oauth/github/callback', methods=['GET'])
def oauth_github_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return _redirect_to_frontend('/login', f'error=github_{error}')
    if not code or not state:
        return _redirect_to_frontend('/login', 'error=missing_params')
    if not _verify_state(state):
        return _redirect_to_frontend('/login', 'error=invalid_state')

    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET')
    if not client_id or not client_secret:
        return _redirect_to_frontend('/login', 'error=oauth_not_configured')

    try:
        r = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={'client_id': client_id, 'client_secret': client_secret, 'code': code},
            timeout=10,
        )
        gh_token = r.json().get('access_token')
        if not gh_token:
            return _redirect_to_frontend('/login', 'error=no_access_token')

        ur = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {gh_token}'},
            timeout=10,
        )
        gh_user = ur.json()
        email = gh_user.get('email')
        if not email:
            er = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {gh_token}'},
                timeout=10,
            )
            if er.status_code == 200:
                emails = er.json()
                for e in emails:
                    if e.get('primary'):
                        email = e.get('email')
                        break
                if not email and emails:
                    email = emails[0].get('email')

        if not email:
            return _redirect_to_frontend('/login', 'error=no_email')

        um = get_user_manager()
        user = um.find_by_email(email)

        if not user:
            if um.count_users() == 0:
                user, err = um.create_user(
                    name=gh_user.get('name') or gh_user.get('login') or 'GitHub User',
                    email=email,
                    password=secrets.token_urlsafe(24),
                    role='admin',
                )
                if err or not user:
                    return _redirect_to_frontend('/login', 'error=create_failed')
            else:
                return _redirect_to_frontend('/login', 'error=no_account_matching_email')

        um.update_tokens(user['user_id'], {'github': gh_token})
        um.update_last_login(user['user_id'])

        session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
        access = um.generate_token(user['user_id'], session_minutes)
        refresh = um.generate_refresh_token(user['user_id'])

        resp = _redirect_to_frontend('/dashboard', 'oauth=github_success')
        _set_auth_cookies(resp, access, refresh)
        return resp
    except Exception as e:
        print(f"[OAUTH-GITHUB] Error: {e}")
        import traceback
        traceback.print_exc()
        return _redirect_to_frontend('/login', 'error=server_error')


# ─── Google OAuth ───
@auth_bp.route('/oauth/google/start', methods=['GET'])
def oauth_google_start():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        return _redirect_to_frontend('/login', 'error=oauth_not_configured')

    state = _create_state()
    backend = os.getenv('BACKEND_URL', 'http://localhost:5000')

    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={backend}/api/auth/oauth/google/callback"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(url)


@auth_bp.route('/oauth/google/callback', methods=['GET'])
def oauth_google_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return _redirect_to_frontend('/login', f'error=google_{error}')
    if not code or not state:
        return _redirect_to_frontend('/login', 'error=missing_params')
    if not _verify_state(state):
        return _redirect_to_frontend('/login', 'error=invalid_state')

    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        return _redirect_to_frontend('/login', 'error=oauth_not_configured')

    try:
        backend = os.getenv('BACKEND_URL', 'http://localhost:5000')

        r = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': f'{backend}/api/auth/oauth/google/callback',
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
        tokens = r.json()
        id_token = tokens.get('id_token')
        if not id_token:
            return _redirect_to_frontend('/login', 'error=no_id_token')

        info_r = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}',
            timeout=10,
        )
        info = info_r.json()
        email = info.get('email')
        if not email:
            return _redirect_to_frontend('/login', 'error=no_email')

        um = get_user_manager()
        user = um.find_by_email(email)

        if not user:
            if um.count_users() == 0:
                user, err = um.create_user(
                    name=info.get('name') or email.split('@')[0],
                    email=email,
                    password=secrets.token_urlsafe(24),
                    role='admin',
                )
                if err or not user:
                    return _redirect_to_frontend('/login', 'error=create_failed')
            else:
                return _redirect_to_frontend('/login', 'error=no_account_matching_email')

        um.update_last_login(user['user_id'])
        session_minutes = user.get('settings', {}).get('sessionTimeout', 30)
        access = um.generate_token(user['user_id'], session_minutes)
        refresh = um.generate_refresh_token(user['user_id'])

        resp = _redirect_to_frontend('/dashboard', 'oauth=google_success')
        _set_auth_cookies(resp, access, refresh)
        return resp
    except Exception as e:
        print(f"[OAUTH-GOOGLE] Error: {e}")
        import traceback
        traceback.print_exc()
        return _redirect_to_frontend('/login', 'error=server_error')