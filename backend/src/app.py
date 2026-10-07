"""
Smart DevOps Backend — Universal Agentic AI Edition
====================================================
Cross-page real-time sync + Level 3 self-learning
+ Aggressive reconnect + Event replay + 2h ping timeout
+ Orphan cloudflared cleanup on startup
+ FULL auto-restore (proxy + backend + tunnel)
+ PREMIUM: CORS with credentials + OAuth endpoints
+ NEW: Cloudflare agent deploy endpoint
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

# ============================================================
# Async mode detection
# ============================================================
async_mode = 'threading'
try:
    from gevent import monkey
    monkey.patch_all(ssl=False)
    import gevent
    async_mode = 'gevent'
    print("OK Using gevent")
except ImportError:
    print("WARN Using threading")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# ============================================================
# Flask App
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['MONGO_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
app.config['MONGODB_DB'] = os.getenv('MONGODB_DB', 'smart_devops')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CORS with credentials support
FRONTEND_ORIGINS = os.getenv(
    'FRONTEND_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS(
    app,
    resources={r"/*": {"origins": FRONTEND_ORIGINS}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
print(f"OK CORS configured for origins: {FRONTEND_ORIGINS}")

# ============================================================
# Socket.IO — with credentials support
# ============================================================
socketio = SocketIO(
    app,
    cors_allowed_origins=FRONTEND_ORIGINS,
    supports_credentials=True,
    ping_timeout=7200,
    ping_interval=60,
    max_http_buffer_size=100 * 1024 * 1024,
    async_mode=async_mode,
    logger=False,
    engineio_logger=False,
)
print(f"OK SocketIO initialized (async_mode={async_mode}, ping_timeout=7200s)")

# ============================================================
# Wire agents + Event Bus
# ============================================================
try:
    from agents.base_agent import set_socketio
    set_socketio(socketio)
    print("OK Socket.IO -> agents connected")
except ImportError as e:
    print(f"WARN Socket to agents: {e}")

try:
    from core.event_bus import set_socketio as set_event_bus_socket
    set_event_bus_socket(socketio)
    print("OK Event Bus -> Socket.IO connected")
except Exception as e:
    print(f"WARN Event Bus: {e}")


def stream_terminal_log(message, log_type="info", sid=None):
    payload = {
        'log': message, 'message': message, 'type': log_type,
        'level': log_type, 'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    if sid:
        socketio.emit('live_log', payload, room=sid)
    else:
        socketio.emit('live_log', payload)


# ============================================================
# Database
# ============================================================
db = None
db_connection = None
try:
    from database.connection import db_connection
    if db_connection.init_app(app):
        print("OK Database connected!")
        db = db_connection.get_db()
        app.mongo = db
    else:
        print("ERROR Database failed!")
        app.mongo = None
except ImportError:
    print("WARN Dummy DB")
    class DummyDB:
        def init_app(self, app): return False
        def get_db(self): return None
        def get_stats(self): return {'status': 'disconnected', 'collections_list': []}
    db_connection = DummyDB()
    db = None
    app.mongo = None

# ============================================================
# Logging
# ============================================================
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)

# ============================================================
# Blueprints
# ============================================================
blueprint_defs = [
    ('api.auth', 'auth_bp', '/api/auth'),
    ('api.assistant', 'assistant_bp', '/api/assistant'),
    ('api.upload', 'upload_bp', '/api/upload'),
    ('api.pipelines', 'pipelines_bp', '/api/pipelines'),
    ('api.infrastructure', 'infrastructure_bp', '/api/infrastructure'),
    ('api.monitoring', 'monitoring_bp', '/api/monitoring'),
    ('api.infra_agent', 'infra_bp', '/api/monitoring/infra'),
    ('api.training', 'training_bp', '/api/training'),
    ('api.settings', 'settings_bp', '/api/settings'),
    ('api.devops', 'devops_bp', '/api/devops'),
]
blueprints_loaded = []
for module_name, bp_name, url_prefix in blueprint_defs:
    try:
        module = __import__(module_name, fromlist=[bp_name])
        bp = getattr(module, bp_name)
        app.register_blueprint(bp, url_prefix=url_prefix)
        blueprints_loaded.append(url_prefix)
        logger.info(f"OK Registered {url_prefix}")
    except (ImportError, AttributeError) as e:
        logger.warning(f"WARN {module_name}: {e}")


# ============================================================
# Intent detection helpers
# ============================================================
def detect_intent(message: str) -> dict:
    text = message.lower().strip()
    if any(w in text for w in ['deploy', 'release', 'publish', 'ship']):
        return {'action': 'deploy', 'target': 'fullstack', 'params': {}}
    if any(w in text for w in ['pipeline', 'ci/cd', 'cicd']):
        return {'action': 'pipeline', 'target': 'fullstack', 'params': {}}
    if any(w in text for w in ['fix', 'repair', 'debug', 'error']):
        return {'action': 'fix', 'target': 'code', 'params': {}}
    if any(w in text for w in ['scan', 'security', 'vulnerability']):
        return {'action': 'scan', 'target': 'code', 'params': {}}
    if any(w in text for w in ['monitor', 'logs', 'metrics']):
        return {'action': 'monitor', 'target': 'infra', 'params': {}}
    return {'action': 'none', 'target': None, 'params': {}}


def build_execution(intent: dict, status: str = 'running', progress: int = 10) -> dict:
    action = intent.get('action', 'task')
    step_map = {
        'deploy': ['Analyze repo', 'Choose provider', 'Clone', 'Deploy', 'Verify'],
        'pipeline': ['Analyze', 'Generate YAML', 'Commit', 'Monitor'],
        'fix': ['Analyze', 'Find files', 'Generate fix', 'Apply', 'Verify'],
        'scan': ['Fetch', 'Scan secrets', 'Scan vulns', 'Analyze'],
        'monitor': ['Fetch', 'Analyze', 'Ready'],
        'none': ['Process'],
    }
    steps = step_map.get(action, ['Process'])
    return {
        'status': status, 'progress': progress, 'duration': '0s',
        'steps': [{'name': s, 'status': 'pending'} for s in steps]
    }


# ============================================================
# Orchestrator (lazy)
# ============================================================
_orchestrator = None


def _get_orchestrator_raw():
    global _orchestrator
    if _orchestrator is None:
        try:
            from agents.orchestrator import Orchestrator
            _orchestrator = Orchestrator()
            print("OK Orchestrator initialized")
        except Exception as e:
            print(f"ERROR Orchestrator: {e}")
            import traceback
            traceback.print_exc()
            return None
    return _orchestrator


def get_orchestrator():
    """Wrapper — also wires Universal Registry."""
    orch = _get_orchestrator_raw()
    if orch and hasattr(orch, 'self_host') and orch.self_host:
        try:
            from core.universal_registry import set_self_host_service
            set_self_host_service(orch.self_host)
        except Exception:
            pass
    return orch


# ============================================================
# NEW: Cloudflare Agent Deploy
# ============================================================
try:
    from agent_deployer import deploy as cloudflare_deploy
    CLOUDFLARE_AGENT_AVAILABLE = True
    print("OK Cloudflare Agent Deployer loaded")
except ImportError as e:
    CLOUDFLARE_AGENT_AVAILABLE = False
    print(f"WARN Cloudflare Agent Deployer not found: {e}")


@app.route('/api/agent/deploy', methods=['POST', 'OPTIONS'])
def agent_deploy():
    """
    Deploy a GitHub repo via Cloudflare Tunnel.
    Body: { "git_url": "https://github.com/user/repo" }
    Returns: { "success": true, "url": "https://repo.deploy.smartdevops.site" }
    """
    if request.method == 'OPTIONS':
        return '', 204

    if not CLOUDFLARE_AGENT_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Cloudflare deployer module not available. Check agent_deployer.py."
        }), 503

    data = request.get_json(silent=True) or {}
    git_url = data.get('git_url') or data.get('repo_url') or data.get('gitUrl')

    if not git_url:
        return jsonify({"success": False, "error": "git_url is required"}), 400

    if not git_url.startswith('http'):
        return jsonify({"success": False, "error": "git_url must be a valid URL"}), 400

    try:
        stream_terminal_log(f"Starting Cloudflare deploy: {git_url}", "info")
        result = cloudflare_deploy(git_url)
        stream_terminal_log(f"Deploy complete: {result.get('url')}", "success")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Agent deploy failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/agent/deployments', methods=['GET'])
def list_deployments():
    """List all active deployments."""
    try:
        from agent_deployer import APPS_DIR
        deployments = []
        if APPS_DIR.exists():
            for file in APPS_DIR.glob("*.json"):
                try:
                    with open(file) as f:
                        deployments.append(json.load(f))
                except Exception:
                    pass
        return jsonify({"success": True, "deployments": deployments}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Orphan cloudflared cleanup on startup
# ============================================================
def cleanup_orphan_tunnels():
    try:
        keep_pids = set()
        deploy_root = os.getenv('SELF_HOST_ROOT', 'D:/dev/final_project/deployments')

        if os.path.isdir(deploy_root):
            for folder in os.listdir(deploy_root):
                info_file = os.path.join(deploy_root, folder, 'tunnel.json')
                if not os.path.exists(info_file):
                    continue
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    pid = info.get('pid')
                    if not pid:
                        continue

                    result = subprocess.run(
                        f'tasklist /FI "PID eq {pid}" /NH',
                        shell=True, capture_output=True, text=True, timeout=5,
                    )
                    if str(pid) in result.stdout:
                        keep_pids.add(int(pid))
                except Exception:
                    pass

        result = subprocess.run(
            'tasklist /FI "IMAGENAME eq cloudflared.exe" /NH',
            shell=True, capture_output=True, text=True, timeout=10,
        )

        killed = 0
        for line in result.stdout.splitlines():
            if 'cloudflared.exe' not in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1])
                if pid in keep_pids:
                    continue
                subprocess.run(
                    f'taskkill /F /PID {pid}',
                    shell=True, capture_output=True, timeout=5,
                )
                killed += 1
            except Exception:
                pass

        if killed:
            print(f"CLEANUP: Killed {killed} orphan cloudflared processes (kept {len(keep_pids)} live)")
        else:
            print(f"CLEANUP: No orphan cloudflared processes (kept {len(keep_pids)} live)")
    except Exception as e:
        print(f"WARN Orphan cleanup error: {e}")


# ============================================================
# Background tasks
# ============================================================
def start_background_tasks():
    import threading
    import time as _time

    cleanup_orphan_tunnels()

    def cleanup_loop():
        _time.sleep(120)
        while True:
            try:
                orch = get_orchestrator()
                if orch and orch.self_host:
                    result = orch.self_host.cleanup_stale(
                        max_age_seconds=7200, keep_latest=2,
                    )
                    removed = result.get('removed', [])
                    if removed:
                        print(f"[AUTO-CLEANUP] Removed {len(removed)}")
            except Exception as e:
                print(f"[AUTO-CLEANUP] {e}")
            _time.sleep(900)

    def restore_all_deployments():
        _time.sleep(5)
        try:
            orch = get_orchestrator()
            if orch and orch.self_host:
                print("[STARTUP] Restoring ALL (proxy + backend + tunnel)...")
                if hasattr(orch.self_host, 'restore_all'):
                    restored = orch.self_host.restore_all()
                    print(f"[STARTUP] Restore summary: {restored}")
                elif hasattr(orch.self_host, 'restore_tunnels'):
                    restored = orch.self_host.restore_tunnels()
                    print(f"[STARTUP] Restored {len(restored) if restored else 0} tunnels")
        except Exception as e:
            print(f"[STARTUP] {e}")

    t1 = threading.Thread(target=cleanup_loop, daemon=True)
    t1.start()
    print("OK Auto-cleanup started")

    t2 = threading.Thread(target=restore_all_deployments, daemon=True)
    t2.start()

    try:
        from api.infra_agent import start_agent
        start_agent()
        print("OK Infra AI Agent started")
    except Exception as e:
        print(f"WARN Infra Agent start failed: {e}")

    try:
        from ml.auto_retrain import start as start_auto_retrain
        start_auto_retrain()
        print("OK Auto-Retrain started")
    except Exception as e:
        print(f"WARN Auto-Retrain failed: {e}")


start_background_tasks()


# ============================================================
# WebSocket Events
# ============================================================
@socketio.on('connect')
def handle_connect():
    logger.info(f"OK Client: {request.sid}")
    join_room(request.sid)
    emit('connected', {
        'message': 'Connected to Smart DevOps Engine',
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    })
    stream_terminal_log("Agent Socket Online...", "success", sid=request.sid)

    try:
        from core.event_bus import get_recent_events
        emit('platform_events_replay', {'events': get_recent_events(30)})
    except Exception:
        pass


@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"BYE Client: {request.sid}")
    leave_room(request.sid)


@socketio.on('client_wake')
def handle_client_wake(data):
    sid = request.sid
    logger.info(f"WAKE Client woke: {sid}")
    try:
        from core.event_bus import get_recent_events
        recent = get_recent_events(50)
        emit('platform_events_replay', {
            'events': recent,
            'reason': 'client_wake',
        })
        stream_terminal_log("Welcome back — state synced", "success", sid=sid)
    except Exception as e:
        logger.warning(f"client_wake replay failed: {e}")


@socketio.on('chat')
def handle_chat(data):
    sid = request.sid
    try:
        message = data.get('message', '')
        user_id = data.get('user_id', 'anonymous')
        project_id = data.get('project_id', 'default_project')
        project_name = data.get('project_name', 'Unknown')
        source = data.get('source', 'unknown')

        logger.info(f"CHAT: {message[:80]}")
        stream_terminal_log(f"Received: '{message[:60]}'", "info", sid=sid)

        orchestrator = get_orchestrator()
        if not orchestrator:
            emit('chat_response', {
                'message': "Agentic AI offline",
                'timestamp': datetime.now().isoformat(),
            }, room=sid)
            return

        stream_terminal_log("Orchestrator processing...", "info", sid=sid)

        result = orchestrator.process(
            {'action': 'chat', 'query': message,
             'project_id': project_id, 'project_name': project_name},
            context={'user_id': user_id, 'sid': sid,
                     'project_id': project_id, 'project_name': project_name,
                     'source': source}
        )

        if isinstance(result, dict):
            reply_text = result.get('response') or result.get('message') or str(result)
            exec_data = result.get('execution')
            if not exec_data:
                intent = detect_intent(message)
                exec_data = build_execution(intent, status='completed', progress=100)
                for s in exec_data['steps']:
                    s['status'] = 'completed'
            if result.get('live_url'):
                exec_data['liveUrl'] = result['live_url']
        else:
            reply_text = str(result)
            exec_data = None

        emit('chat_response', {
            'message': reply_text, 'execution': exec_data,
            'intent': detect_intent(message),
            'result_type': result.get('type') if isinstance(result, dict) else None,
            'timestamp': datetime.now().isoformat(),
        }, room=sid)

        if (isinstance(result, dict) and
                result.get('type') in ('deploy', 'pipeline') and
                result.get('success')):
            emit('deploy_complete', {
                'deployId': result.get('deploy_id') or f"deploy-{int(datetime.now().timestamp())}",
                'type': result.get('type', 'deploy'),
                'liveUrl': result.get('live_url') or result.get('url'),
                'buildMethod': result.get('provider', 'unknown'),
                'fixesApplied': result.get('auto_fixes_applied', 0),
                'duration': result.get('duration', '0s'),
                'steps': exec_data.get('steps', []) if exec_data else [],
                'summary': f"Deployed via {result.get('provider', 'unknown')}",
                'timestamp': datetime.now().isoformat(),
            }, room=sid)

        stream_terminal_log("Response sent", "success", sid=sid)

    except Exception as e:
        logger.error(f"ERROR Chat: {e}")
        import traceback
        traceback.print_exc()
        emit('chat_response', {'error': str(e), 'timestamp': datetime.now().isoformat()}, room=sid)


@socketio.on('devops_action')
def handle_quick_action(data):
    sid = request.sid
    action_type = data.get('action')
    project_id = data.get('project_id', 'default_project')
    project_name = data.get('project_name', 'Unknown')
    repo_url = data.get('repo_url') or data.get('repoUrl')

    stream_terminal_log(f"Action: {action_type.upper()}", "info", sid=sid)

    orchestrator = get_orchestrator()
    if not orchestrator:
        emit('action_response', {'status': 'failed', 'error': 'Orchestrator not available'}, room=sid)
        return

    try:
        payload = {'action': action_type, 'repo_url': repo_url,
                   'project_id': project_id, 'project_name': project_name, 'data': data}

        if action_type == 'deploy':
            payload['mode'] = data.get('mode', 'self-deploy')
            payload['fullstack'] = True
            payload['provider'] = data.get('provider', 'auto')
            payload['deploy_method'] = data.get('deploy_method', 'self-host')
            payload['skip_pipeline'] = True
        elif action_type == 'pipeline':
            payload['mode'] = data.get('mode', 'ci-cd+deploy')
            payload['deploy_method'] = data.get('deploy_method', 'self-host')
            payload['provider'] = data.get('provider', 'self-host')
            payload['max_fix_attempts'] = data.get('max_fix_attempts', 50)

        result = orchestrator.process(payload, context={
            'sid': sid, 'project_id': project_id,
            'project_name': project_name, 'repo_url': repo_url,
        })

        emit('action_response', {
            'status': 'success' if (isinstance(result, dict) and result.get('success', True)) else 'failed',
            'action': action_type, 'result': result,
            'message': result.get('response', '') if isinstance(result, dict) else '',
            'timestamp': datetime.now().isoformat(),
        }, room=sid)

    except Exception as e:
        logger.error(f"Action: {e}")
        emit('action_response', {'status': 'failed', 'error': str(e)}, room=sid)


# ============================================================
# Health & Root
# ============================================================
@app.route('/api/health')
def health_check():
    db_stats = db_connection.get_stats() if db_connection else {'status': 'disconnected'}
    agent_count = 0
    try:
        orch = get_orchestrator()
        if orch:
            agent_count = len(orch.agents)
    except Exception:
        pass

    infra_agent_info = {}
    try:
        from api.infra_agent import agent_state_data
        infra_agent_info = agent_state_data()
    except Exception:
        pass

    return jsonify({
        'status': 'healthy',
        'database': db_stats.get('status', 'unknown'),
        'registered_blueprints': blueprints_loaded,
        'agents': agent_count,
        'infra_agent': infra_agent_info,
        'timestamp': datetime.now().isoformat(),
        'version': '3.1.0',
        'async_mode': async_mode,
        'cloudflare_agent': CLOUDFLARE_AGENT_AVAILABLE,
        'tokens': {
            'github': bool(os.getenv('GITHUB_TOKEN')),
            'groq': bool(os.getenv('GROQ_API_KEY')),
            'vercel': bool(os.getenv('VERCEL_TOKEN')),
            'render': bool(os.getenv('RENDER_API_KEY')),
            'netlify': bool(os.getenv('NETLIFY_TOKEN')),
            'cloudflare': bool(os.getenv('CLOUDFLARE_API_TOKEN')),
        },
    })


@app.route('/')
def root():
    return jsonify({
        'name': 'Smart DevOps Backend — Universal',
        'status': 'running', 'version': '3.1.0'
    })


# ============================================================
# Run
# ============================================================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n{'='*60}")
    print(f"  Smart DevOps Backend — Universal Agentic")
    print(f"  Port: {port} | Async: {async_mode}")
    print(f"{'='*60}\n")

    if async_mode == 'gevent':
        try:
            from gevent import pywsgi
            from geventwebsocket.handler import WebSocketHandler
            server = pywsgi.WSGIServer(
                ('0.0.0.0', port), app,
                handler_class=WebSocketHandler
            )
            print(f"OK gevent WSGIServer starting...\n")
            server.serve_forever()
        except ImportError:
            socketio.run(app, host='0.0.0.0', port=port,
                         debug=False, allow_unsafe_werkzeug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=port,
                     debug=False, allow_unsafe_werkzeug=True)