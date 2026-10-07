"""
DevOps API — Complete REST endpoints
=====================================
All DevOps buttons + unified actions.
All actions route through Orchestrator → Agents.
"""

import os
import re
import time
import traceback
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

devops_bp = Blueprint('devops', __name__)

_orchestrator = None


def get_orchestrator():
    """Lazy init orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        try:
            from agents.orchestrator import Orchestrator
            _orchestrator = Orchestrator()
            print("✅ Orchestrator initialized for DevOps API")
        except Exception as e:
            print(f"❌ Orchestrator init failed: {e}")
            traceback.print_exc()
            return None
    return _orchestrator


# ============================================
# 🧠 UNIVERSAL GITHUB URL PARSER
# ============================================
def parse_github_url(raw_url: str, explicit_branch: str = None):
    """Parse ANY GitHub URL format → {owner, repo, branch, source}."""
    if not raw_url:
        return None

    raw = raw_url.strip().rstrip('/')
    if raw.endswith('.git'):
        raw = raw[:-4]

    if not raw.startswith('http'):
        if '/' in raw and not raw.startswith('github.com'):
            parts = raw.split('/')
            if len(parts) >= 2:
                raw = f"https://github.com/{parts[0]}/{parts[1]}"
                if len(parts) >= 4 and parts[2] in ('tree', 'blob'):
                    raw += f"/tree/{parts[3]}"
        else:
            return None

    m = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+))?',
        raw
    )
    if not m:
        return None

    owner = m.group(1)
    repo = m.group(2)
    url_branch = m.group(3)

    target_branch = explicit_branch or url_branch

    default_branch = None
    if not target_branch:
        default_branch = _get_default_branch(owner, repo)
        target_branch = default_branch or 'main'

    return {
        'owner': owner,
        'repo': repo,
        'branch': target_branch,
        'default_branch': default_branch,
        'source': 'explicit' if explicit_branch else ('url' if url_branch else 'auto'),
    }


def _get_default_branch(owner: str, repo: str) -> str:
    """Query GitHub API for default branch."""
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    try:
        r = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers=headers, timeout=10,
        )
        if r.status_code == 200:
            return r.json().get('default_branch', 'main')
    except Exception:
        pass
    return 'main'


# ============================================
# 🚀 DEPLOY
# ============================================
@devops_bp.route('/deploy', methods=['POST', 'OPTIONS'])
def deploy():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    explicit_branch = data.get('branch')
    project_name = data.get('project_name', 'default')
    deploy_type = data.get('deploy_type', 'auto')
    provider = data.get('provider', 'self-host')
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    sid = data.get('sid')

    if not raw_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    parsed = parse_github_url(raw_url, explicit_branch)
    if not parsed:
        return jsonify({'success': False, 'error': 'Invalid GitHub URL'}), 400

    repo_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}"
    branch = parsed['branch']

    print(f"[DEVOPS] Deploy → {repo_url} @ {branch} (source: {parsed['source']})", flush=True)

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='deploy', repo_url=repo_url, provider=provider,
            user_id=user_id, project_id=project_id, project_name=project_name,
            extra={'deploy_type': deploy_type, 'branch': branch},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({
            'action': 'deploy',
            'repo_url': repo_url,
            'branch': branch,
            'project_name': project_name,
            'deploy_type': deploy_type,
            'provider': provider,
            'deploy_method': provider,
            'skip_pipeline': True,
            'fullstack': deploy_type in ('auto', 'fullstack'),
        }, context={'sid': sid, 'user_id': user_id,
                    'project_id': project_id, 'project_name': project_name})

        if action_id:
            try:
                from services.action_store import action_store
                if result.get('success'):
                    action_store.update_action(
                        action_id, status='success', progress=100,
                        url=result.get('url') or result.get('live_url'),
                        result=result,
                    )
                else:
                    action_store.update_action(
                        action_id, status='failed', progress=100,
                        error=result.get('error', 'Unknown'),
                    )
            except Exception:
                pass

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        if action_id:
            try:
                from services.action_store import action_store
                action_store.update_action(action_id, status='failed', error=str(e)[:200])
            except Exception:
                pass
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ⚙️ PIPELINE
# ============================================
@devops_bp.route('/pipeline', methods=['POST', 'OPTIONS'])
def create_pipeline():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    explicit_branch = data.get('branch')
    mode = data.get('mode', 'ci-cd+deploy')
    deploy_method = data.get('deploy_method', 'self-host')
    provider = data.get('provider') or deploy_method
    max_attempts = data.get('max_fix_attempts', 50)
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    project_name = data.get('project_name', 'Unknown')
    sid = data.get('sid')

    if not raw_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    parsed = parse_github_url(raw_url, explicit_branch)
    if not parsed:
        return jsonify({'success': False, 'error': 'Invalid GitHub URL'}), 400

    repo_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}"
    branch = parsed['branch']

    mode_config = {
        'ci-cd-only':     {'run_pipeline': True,  'auto_deploy': False, 'skip_pipeline': False},
        'ci-cd+deploy':   {'run_pipeline': True,  'auto_deploy': True,  'skip_pipeline': False},
        'self-deploy':    {'run_pipeline': False, 'auto_deploy': True,  'skip_pipeline': True},
        'custom-deploy':  {'run_pipeline': False, 'auto_deploy': True,  'skip_pipeline': True},
    }

    if mode not in mode_config:
        return jsonify({'success': False, 'error': f'Invalid mode: {mode}'}), 400

    cfg = mode_config[mode]

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='pipeline', repo_url=repo_url, provider=provider,
            user_id=user_id, project_id=project_id, project_name=project_name,
            extra={'mode': mode, 'max_attempts': max_attempts, 'branch': branch},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({
            'action': 'pipeline' if cfg['run_pipeline'] else 'deploy',
            'repo_url': repo_url,
            'branch': branch,
            'mode': mode,
            'deploy_method': deploy_method,
            'provider': provider,
            'max_fix_attempts': max_attempts,
            'auto_deploy': cfg['auto_deploy'],
            'skip_pipeline': cfg['skip_pipeline'],
            'run_pipeline': cfg['run_pipeline'],
        }, context={'sid': sid, 'user_id': user_id,
                    'project_id': project_id, 'project_name': project_name})

        if action_id:
            try:
                from services.action_store import action_store
                if result.get('success'):
                    action_store.update_action(
                        action_id, status='success', progress=100,
                        url=result.get('live_url') or result.get('url'),
                        result=result,
                    )
                else:
                    action_store.update_action(action_id, status='failed',
                                               error=result.get('error', 'Unknown'))
            except Exception:
                pass

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        if action_id:
            try:
                from services.action_store import action_store
                action_store.update_action(action_id, status='failed', error=str(e)[:200])
            except Exception:
                pass
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🛡️ SECURITY — Agent-powered
# ============================================
@devops_bp.route('/action/security', methods=['POST', 'OPTIONS'])
def quick_security():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    explicit_branch = data.get('branch')
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    project_name = data.get('project_name', 'Unknown')
    sid = data.get('sid')

    if not raw_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    parsed = parse_github_url(raw_url, explicit_branch)
    if not parsed:
        return jsonify({'success': False, 'error': 'Invalid GitHub URL'}), 400

    owner, repo, branch = parsed['owner'], parsed['repo'], parsed['branch']
    print(f"[SECURITY] → {owner}/{repo} @ {branch}", flush=True)

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='security',
            repo_url=f"https://github.com/{owner}/{repo}",
            provider='security', user_id=user_id,
            project_id=project_id, project_name=project_name,
            extra={'branch': branch},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process(
            {
                'action': 'security',
                'repo_url': f"https://github.com/{owner}/{repo}",
                'branch': branch,
            },
            context={'sid': sid, 'user_id': user_id,
                     'project_id': project_id, 'project_name': project_name},
        )

        if action_id:
            try:
                from services.action_store import action_store
                if result.get('success'):
                    action_store.update_action(
                        action_id, status='success', progress=100,
                        result=result.get('result', {}),
                    )
                else:
                    action_store.update_action(
                        action_id, status='failed', progress=100,
                        error=result.get('error', 'Unknown'),
                    )
            except Exception:
                pass

        return jsonify({
            'success': result.get('success', False),
            'action_id': action_id,
            'response': result.get('response', ''),
            'result': result.get('result', {}),
            'branch': branch,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🩺 FIX CODE — Agent-powered
# ============================================
@devops_bp.route('/action/fix-code', methods=['POST', 'OPTIONS'])
def quick_fix_code():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    explicit_branch = data.get('branch')
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    project_name = data.get('project_name', 'Unknown')
    sid = data.get('sid')

    if not raw_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    parsed = parse_github_url(raw_url, explicit_branch)
    if not parsed:
        return jsonify({'success': False, 'error': 'Invalid GitHub URL'}), 400

    owner, repo, branch = parsed['owner'], parsed['repo'], parsed['branch']
    print(f"[FIXER] → {owner}/{repo} @ {branch}", flush=True)

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='fix_code',
            repo_url=f"https://github.com/{owner}/{repo}",
            provider='fixer', user_id=user_id,
            project_id=project_id, project_name=project_name,
            extra={'branch': branch},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process(
            {
                'action': 'fix_code',
                'repo_url': f"https://github.com/{owner}/{repo}",
                'branch': branch,
            },
            context={'sid': sid, 'user_id': user_id,
                     'project_id': project_id, 'project_name': project_name},
        )

        if action_id:
            try:
                from services.action_store import action_store
                if result.get('success'):
                    action_store.update_action(
                        action_id, status='success', progress=100,
                        url=result.get('pr_url'),
                        result=result.get('result', {}),
                    )
                else:
                    action_store.update_action(
                        action_id, status='failed', progress=100,
                        error=result.get('error', 'Unknown'),
                    )
            except Exception:
                pass

        return jsonify({
            'success': result.get('success', False),
            'action_id': action_id,
            'response': result.get('response', ''),
            'pr_url': result.get('pr_url'),
            'branch': branch,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📊 MONITOR — Agent-powered
# ============================================
@devops_bp.route('/action/monitor', methods=['POST', 'OPTIONS'])
def quick_monitor():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    target_url = data.get('url')
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    project_name = data.get('project_name', 'Unknown')
    sid = data.get('sid')

    if not raw_url and not target_url:
        return jsonify({'success': False, 'error': 'repo_url or url required'}), 400

    # If no URL provided, try to find from deployments
    if not target_url and raw_url:
        parsed = parse_github_url(raw_url)
        if parsed:
            try:
                from services.self_host_service import SelfHostService
                shs = SelfHostService()
                for d in shs.list_deployments().values():
                    if d.get('repo_url') and parsed['repo'] in d.get('repo_url'):
                        target_url = d.get('url')
                        break
            except Exception:
                pass

    if not target_url:
        return jsonify({
            'success': False,
            'error': 'No live URL found — deploy first or pass url param',
        }), 400

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='monitor',
            repo_url=raw_url or target_url,
            provider='monitor', user_id=user_id,
            project_id=project_id, project_name=project_name,
            extra={'url': target_url},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process(
            {'action': 'monitor', 'url': target_url, 'repo_url': raw_url},
            context={'sid': sid, 'user_id': user_id,
                     'project_id': project_id, 'project_name': project_name},
        )

        if action_id:
            try:
                from services.action_store import action_store
                action_store.update_action(
                    action_id,
                    status='success' if result.get('success') else 'failed',
                    progress=100, url=target_url,
                    result={'url': target_url},
                )
            except Exception:
                pass

        return jsonify({
            'success': result.get('success', False),
            'action_id': action_id,
            'response': result.get('response', ''),
            'url': target_url,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📈 SCALE — Agent-powered
# ============================================
@devops_bp.route('/action/scale', methods=['POST', 'OPTIONS'])
def quick_scale():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    raw_url = data.get('repo_url')
    service = data.get('service')
    replicas = int(data.get('replicas', 3))
    user_id = data.get('user_id', 'anonymous')
    project_id = data.get('project_id', 'default')
    project_name = data.get('project_name', 'Unknown')
    sid = data.get('sid')

    if not raw_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    parsed = parse_github_url(raw_url)
    if not parsed:
        return jsonify({'success': False, 'error': 'Invalid GitHub URL'}), 400

    if not service:
        service = parsed['repo'].lower().replace('_', '-')

    try:
        from services.action_store import action_store
        action_id = action_store.start_action(
            action_type='scale',
            repo_url=f"https://github.com/{parsed['owner']}/{parsed['repo']}",
            provider='infrastructure', user_id=user_id,
            project_id=project_id, project_name=project_name,
            extra={'replicas': replicas},
        )
    except Exception:
        action_id = None

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process(
            {
                'action': 'scale',
                'repo_url': f"https://github.com/{parsed['owner']}/{parsed['repo']}",
                'service': service,
                'replicas': replicas,
            },
            context={'sid': sid, 'user_id': user_id,
                     'project_id': project_id, 'project_name': project_name},
        )

        if action_id:
            try:
                from services.action_store import action_store
                action_store.update_action(
                    action_id,
                    status='success' if result.get('success') else 'failed',
                    progress=100,
                    result=result.get('result', {}),
                )
            except Exception:
                pass

        return jsonify({
            'success': result.get('success', False),
            'action_id': action_id,
            'response': result.get('response', ''),
            'service': service,
            'replicas': replicas,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📊 MONITOR (existing URL-only)
# ============================================
@devops_bp.route('/monitor', methods=['POST', 'OPTIONS'])
def monitor():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    url = data.get('url')
    sid = data.get('sid')

    if not url:
        return jsonify({'success': False, 'error': 'url required'}), 400

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({'action': 'monitor', 'url': url},
                              context={'sid': sid})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🩺 FIX (existing)
# ============================================
@devops_bp.route('/fix', methods=['POST', 'OPTIONS'])
def auto_fix():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    repo_url = data.get('repo_url')
    error_message = data.get('error_message', '')
    error_logs = data.get('error_logs', '')
    sid = data.get('sid')

    if not repo_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({
            'action': 'fix',
            'repo_url': repo_url,
            'error_message': error_message,
            'error_logs': error_logs,
        }, context={'sid': sid})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📋 ANALYZE
# ============================================
@devops_bp.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    repo_url = data.get('repo_url')
    sid = data.get('sid')

    if not repo_url:
        return jsonify({'success': False, 'error': 'repo_url required'}), 400

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({'action': 'analyze', 'repo_url': repo_url},
                              context={'sid': sid})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🎯 FIX CODE snippet (existing)
# ============================================
@devops_bp.route('/fix-code', methods=['POST', 'OPTIONS'])
def fix_code():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    code = data.get('code', '')
    error = data.get('error', '')
    language = data.get('language')
    sid = data.get('sid')

    if not code:
        return jsonify({'success': False, 'error': 'code required'}), 400

    orch = get_orchestrator()
    if not orch:
        return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

    try:
        result = orch.process({
            'action': 'fix_code',
            'code': code,
            'error': error,
            'language': language,
        }, context={'sid': sid})
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📊 STATUS
# ============================================
@devops_bp.route('/status', methods=['GET', 'OPTIONS'])
def status():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        orch = get_orchestrator()
        if not orch:
            return jsonify({'success': False, 'error': 'Orchestrator not available'}), 500

        agent_status = {}
        for name, agent in orch.agents.items():
            try:
                agent_status[name] = {
                    'name': agent.name,
                    'state': 'ready' if not agent.is_busy else 'busy',
                    'metrics': agent.get_metrics(),
                }
            except Exception:
                agent_status[name] = {'name': agent.name, 'state': 'unknown'}

        deployments = {}
        try:
            if orch.self_host:
                deployments = orch.self_host.list_deployments()
        except Exception:
            pass

        return jsonify({
            'success': True,
            'orchestrator': {
                'name': orch.name,
                'agents_count': len(orch.agents),
                'metrics': orch.get_metrics(),
            },
            'agents': agent_status,
            'deployments': deployments,
            'deployment_count': len(deployments),
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📋 LIST DEPLOYMENTS
# ============================================
@devops_bp.route('/deployments', methods=['GET', 'OPTIONS'])
def list_deployments():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        orch = get_orchestrator()
        if not orch or not orch.self_host:
            return jsonify({'success': True, 'deployments': {}, 'count': 0})

        deployments = orch.self_host.list_deployments()
        return jsonify({
            'success': True,
            'deployments': deployments,
            'count': len(deployments),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'deployments': {}, 'count': 0}), 500


# ============================================
# 🛑 STOP DEPLOY
# ============================================
@devops_bp.route('/stop-deploy/<deploy_id>', methods=['POST', 'OPTIONS'])
def stop_deploy(deploy_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        orch = get_orchestrator()
        if not orch or not orch.self_host:
            return jsonify({'success': False, 'error': 'Self-host not available'}), 500

        result = orch.self_host.stop_deployment(deploy_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🗑️ DELETE DEPLOY
# ============================================
@devops_bp.route('/delete-deploy/<deploy_id>', methods=['POST', 'OPTIONS', 'DELETE'])
def delete_deploy(deploy_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        orch = get_orchestrator()
        if not orch or not orch.self_host:
            return jsonify({'success': False, 'error': 'Self-host not available'}), 500

        result = orch.self_host.delete_deployment(deploy_id)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🎯 MODES
# ============================================
@devops_bp.route('/modes', methods=['GET', 'OPTIONS'])
def list_modes():
    if request.method == 'OPTIONS':
        return '', 204

    return jsonify({
        'success': True,
        'modes': [
            {'id': 'ci-cd-only', 'label': 'CI/CD Only',
             'description': 'Run CI/CD pipeline only — no deploy',
             'icon': '🔧', 'auto_deploy': False, 'run_pipeline': True},
            {'id': 'self-deploy', 'label': 'Self-Deploy Only',
             'description': 'Deploy directly — no CI/CD',
             'icon': '🚀', 'auto_deploy': True, 'run_pipeline': False},
            {'id': 'ci-cd+deploy', 'label': 'CI/CD + Auto-Deploy',
             'description': 'Full pipeline + auto-deploy (recommended)',
             'icon': '⚡', 'auto_deploy': True, 'run_pipeline': True,
             'recommended': True},
        ],
        'providers': [
            {'id': 'self-host', 'label': 'Self-Host (Agent)', 'icon': '🤖'},
        ],
    })


# ============================================
# 🎯 UNIFIED ACTIONS
# ============================================
@devops_bp.route('/actions', methods=['GET', 'OPTIONS'])
def list_actions():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.action_store import action_store
        action_type = request.args.get('type')
        status_q = request.args.get('status')
        limit = int(request.args.get('limit', 100))

        actions = action_store.list_actions(
            action_type=action_type, status=status_q, limit=limit,
        )
        return jsonify({'success': True, 'actions': actions, 'count': len(actions)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e), 'actions': [], 'count': 0}), 500


@devops_bp.route('/actions/<action_id>', methods=['GET', 'OPTIONS'])
def get_action(action_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.action_store import action_store
        action = action_store.get_action(action_id)
        if not action:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@devops_bp.route('/actions/<action_id>', methods=['DELETE', 'OPTIONS'])
def delete_action(action_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.action_store import action_store
        ok = action_store.delete_action(action_id)
        return jsonify({'success': ok})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@devops_bp.route('/actions/cleanup', methods=['POST', 'OPTIONS'])
def cleanup_actions():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.action_store import action_store
        data = request.get_json() or {}
        max_age = data.get('max_age_seconds', 7200)
        removed = action_store.cleanup_old(max_age_seconds=max_age)
        return jsonify({'success': True, 'removed': removed, 'count': len(removed)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📊 DISK USAGE
# ============================================
@devops_bp.route('/disk-usage', methods=['GET', 'OPTIONS'])
def disk_usage():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        orch = get_orchestrator()
        if not orch or not orch.self_host:
            return jsonify({'success': False, 'error': 'Self-host not available'}), 500

        root = orch.self_host.deploy_root
        cache = orch.self_host.cache_root

        def get_size(path):
            total = 0
            if os.path.exists(path):
                for r, d, files in os.walk(path):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(r, f))
                        except Exception:
                            pass
            return total

        total_size = get_size(root)
        cache_size = get_size(cache)

        return jsonify({
            'success': True,
            'deployments_mb': round(total_size / (1024 * 1024), 2),
            'cache_mb': round(cache_size / (1024 * 1024), 2),
            'total_mb': round((total_size + cache_size) / (1024 * 1024), 2),
            'deployments': len(orch.self_host.list_deployments()),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🧹 CLEANUP
# ============================================
@devops_bp.route('/cleanup', methods=['POST', 'OPTIONS'])
def cleanup():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}
    keep_latest = data.get('keep_latest', 2)
    max_age = data.get('max_age_seconds', 7200)

    try:
        orch = get_orchestrator()
        if not orch or not orch.self_host:
            return jsonify({'success': False, 'error': 'Self-host not available'}), 500

        result = orch.self_host.cleanup_stale(
            max_age_seconds=max_age, keep_latest=keep_latest,
        )
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 💚 HEALTH
# ============================================
@devops_bp.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return '', 204

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
    })