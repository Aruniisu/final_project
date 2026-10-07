"""
Pipelines API — Reads from SelfHostService Registry
====================================================
Serves pipeline/deploy data from the self-host registry.
Each deployment is a separate pipeline entry with its own URL.

NEW: /create endpoint routes through Orchestrator → PipelineAgent
     (same logic as chat — ci-cd+deploy mode)
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json
import time
import uuid
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pipelines_bp = Blueprint('pipelines', __name__)

SELF_HOST_ROOT = os.getenv('SELF_HOST_ROOT', 'D:/dev/final_project/deployments')
REGISTRY_FILE = os.path.join(SELF_HOST_ROOT, '_registry.json')


def _load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {}
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as e:
        print(f"[PIPELINES] Registry JSON corrupt: {e}")
        return {}
    except Exception as e:
        print(f"[PIPELINES] Registry read error: {e}")
        return {}


def _normalize_status(s):
    s = str(s or '').lower()
    if s in ('success', 'live', 'completed', 'running'):
        return 'success'
    if s in ('failed', 'error', 'crashed'):
        return 'failed'
    if s in ('deploying', 'in_progress', 'building'):
        return 'running'
    if s in ('stopped', 'inactive'):
        return 'stopped'
    return 'pending'


def _format_duration(d):
    start = d.get('deployed_at')
    if not start:
        return '—'
    end = d.get('completed_at') or time.time()
    try:
        secs = int(float(end) - float(start))
        if secs < 0:
            return '—'
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        rem = secs % 60
        return f"{mins}m {rem}s"
    except Exception:
        return '—'


def _format_time(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(float(ts)).isoformat()
    except Exception:
        return None


def _build_steps(d, pipeline_status):
    fe_ready = bool(d.get('frontend_ready'))
    be_ready = bool(d.get('backend_ready'))
    built = fe_ready or be_ready

    if pipeline_status == 'success':
        clone_status = 'completed'
        build_status = 'completed'
        deploy_status = 'completed'
    elif pipeline_status == 'running':
        clone_status = 'completed'
        build_status = 'running' if not built else 'completed'
        deploy_status = 'running' if built else 'pending'
    elif pipeline_status == 'failed':
        clone_status = 'completed'
        build_status = 'completed' if built else 'failed'
        deploy_status = 'failed' if built else 'pending'
    else:
        clone_status = build_status = deploy_status = 'pending'

    return [
        {'name': 'Clone',  'status': clone_status,  'duration': '—'},
        {'name': 'Build',  'status': build_status,  'duration': '—'},
        {'name': 'Deploy', 'status': deploy_status, 'duration': '—'},
    ]


# ============================================
# GET / — List all pipelines
# ============================================
@pipelines_bp.route('/', methods=['GET'])
def get_pipelines():
    registry = _load_registry()
    pipelines = []

    for deploy_id, d in registry.items():
        if not isinstance(d, dict):
            continue

        owner = d.get('owner', '')
        repo = d.get('repo', '')
        repo_full = f"{owner}/{repo}".strip('/') or deploy_id
        pipeline_status = _normalize_status(d.get('status'))
        url = d.get('url') or d.get('live_url') or None

        pipelines.append({
            'id': deploy_id,
            'name': repo_full,
            'repo': repo_full,
            'repo_url': d.get('repo_url'),
            'url': url,
            'liveUrl': url,
            'commit': d.get('branch', 'main'),
            'status': pipeline_status,
            'progress': 100 if pipeline_status == 'success' else (
                60 if pipeline_status == 'running' else 0
            ),
            'duration': _format_duration(d),
            'type': d.get('deploy_type', 'auto'),
            'provider': 'self-host',
            'frontend_ready': d.get('frontend_ready', False),
            'backend_ready': d.get('backend_ready', False),
            'steps': _build_steps(d, pipeline_status),
            'createdAt': _format_time(d.get('deployed_at')),
            'completedAt': _format_time(d.get('completed_at')),
        })

    pipelines.sort(key=lambda p: p.get('createdAt') or '', reverse=True)
    return jsonify(pipelines), 200


# ============================================
# GET /<pipeline_id> — Pipeline details
# ============================================
@pipelines_bp.route('/<pipeline_id>', methods=['GET'])
def get_pipeline_details(pipeline_id):
    registry = _load_registry()
    d = registry.get(pipeline_id)

    if not d:
        return jsonify({'success': False, 'error': 'Pipeline not found'}), 404

    owner = d.get('owner', '')
    repo = d.get('repo', '')
    repo_full = f"{owner}/{repo}".strip('/') or pipeline_id
    pipeline_status = _normalize_status(d.get('status'))
    url = d.get('url') or d.get('live_url')

    return jsonify({
        'id': pipeline_id,
        'name': repo_full,
        'repo': repo_full,
        'url': url,
        'liveUrl': url,
        'status': pipeline_status,
        'progress': 100 if pipeline_status == 'success' else 0,
        'duration': _format_duration(d),
        'type': d.get('deploy_type', 'auto'),
        'steps': _build_steps(d, pipeline_status),
        'logs': [],
        'triggeredBy': 'Agent',
        'branch': d.get('branch', 'main'),
        'commit': 'main',
        'createdAt': _format_time(d.get('deployed_at')),
    }), 200


# ============================================
# GET /<pipeline_id>/logs
# ============================================
@pipelines_bp.route('/<pipeline_id>/logs', methods=['GET'])
def get_pipeline_logs(pipeline_id):
    logs = []
    deploy_dir = os.path.join(SELF_HOST_ROOT, pipeline_id)
    for log_name in ['backend.log', 'proxy.log', 'build.log']:
        log_file = os.path.join(deploy_dir, log_name)
        if not os.path.exists(log_file):
            continue
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()[-100:]
            for line in lines:
                logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': line.rstrip(),
                })
        except Exception:
            pass
    return jsonify(logs), 200


# ============================================
# POST /<pipeline_id>/trigger
# ============================================
@pipelines_bp.route('/<pipeline_id>/trigger', methods=['POST'])
def trigger_pipeline(pipeline_id):
    return jsonify({
        'success': True,
        'message': f'Pipeline {pipeline_id} triggered',
        'pipeline_id': pipeline_id,
        'status': 'running',
    }), 200


# ============================================
# POST /<pipeline_id>/retry
# ============================================
@pipelines_bp.route('/<pipeline_id>/retry', methods=['POST'])
def retry_pipeline(pipeline_id):
    try:
        from app import get_orchestrator
        orch = get_orchestrator()
        if not orch:
            return jsonify({'success': False, 'error': 'Orchestrator offline'}), 500

        registry = _load_registry()
        d = registry.get(pipeline_id)
        if not d:
            return jsonify({'success': False, 'error': 'Pipeline not found'}), 404

        result = orch.process({
            'action': 'deploy',
            'repo_url': d.get('repo_url'),
            'mode': 'self-deploy',
            'provider': 'auto',
        }, context={'source': 'retry'})

        return jsonify({
            'success': True,
            'message': f'Pipeline {pipeline_id} retry started',
            'pipeline_id': pipeline_id,
            'result': result,
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# POST /<pipeline_id>/cancel
# ============================================
@pipelines_bp.route('/<pipeline_id>/cancel', methods=['POST'])
def cancel_pipeline(pipeline_id):
    return jsonify({
        'success': True,
        'message': f'Pipeline {pipeline_id} cancelled',
        'pipeline_id': pipeline_id,
    }), 200


# ============================================
# POST / — Create pipeline (via Orchestrator)
# ============================================
@pipelines_bp.route('/', methods=['POST'])
@pipelines_bp.route('/create', methods=['POST'])
def create_pipeline():
    """
    Create a new pipeline via Orchestrator → PipelineAgent.
    
    Payload:
        repo_url (required): GitHub repo URL
        mode: 'ci-cd+deploy' | 'ci-cd-only' | 'self-deploy' | 'custom-deploy'
              (default: 'ci-cd+deploy')
        deploy_method: 'self-host' (default)
        max_fix_attempts: int (default 50)
        auto_deploy: bool (default: True)
        run_pipeline: bool (default: True)
    
    Same logic as chat: 'Create pipeline for <url>'
    """
    data = request.json or {}

    # ⭐ Extract repo_url (support multiple key names)
    repo_url = (
        data.get('repo_url')
        or data.get('repoUrl')
        or data.get('git_url')
    )

    if not repo_url:
        return jsonify({
            'success': False,
            'error': 'repo_url is required',
        }), 400

    if 'github.com' not in repo_url:
        return jsonify({
            'success': False,
            'error': 'Only GitHub URLs are supported',
        }), 400

    # ⭐ Extract mode + parameters
    mode = data.get('mode', 'ci-cd+deploy')
    deploy_method = data.get('deploy_method') or data.get('deployMethod') or 'self-host'

    try:
        max_attempts = int(
            data.get('max_fix_attempts')
            or data.get('maxAttempts')
            or 50
        )
    except (ValueError, TypeError):
        max_attempts = 50

    # ⭐ Derive auto_deploy / run_pipeline from mode (with overrides)
    if 'auto_deploy' in data:
        auto_deploy = bool(data.get('auto_deploy'))
    else:
        auto_deploy = mode in ('ci-cd+deploy', 'self-deploy', 'custom-deploy')

    if 'run_pipeline' in data:
        run_pipeline = bool(data.get('run_pipeline'))
    else:
        run_pipeline = mode in ('ci-cd-only', 'ci-cd+deploy')

    # ⭐ Route through Orchestrator (same as chat)
    try:
        from app import get_orchestrator
        orch = get_orchestrator()

        if not orch:
            return jsonify({
                'success': False,
                'error': 'Orchestrator offline',
            }), 500

        result = orch.process(
            {
                'action': 'pipeline',
                'repo_url': repo_url,
                'mode': mode,
                'deploy_method': deploy_method,
                'provider': deploy_method,
                'max_fix_attempts': max_attempts,
                'auto_deploy': auto_deploy,
                'run_pipeline': run_pipeline,
            },
            context={
                'source': 'pipeline_page',
                'sid': data.get('sid'),
            },
        )

        if not isinstance(result, dict):
            result = {'success': False, 'error': 'Invalid result'}

        return jsonify({
            'success': bool(result.get('success', False)),
            'pipeline_id': result.get('deploy_id'),
            'message': result.get('response', 'Pipeline created'),
            'live_url': result.get('live_url') or result.get('url'),
            'url': result.get('url') or result.get('live_url'),
            'status': result.get('status', 'completed'),
            'result': result,
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500


# ============================================
# DELETE /<pipeline_id>
# ============================================
@pipelines_bp.route('/<pipeline_id>', methods=['DELETE'])
def delete_pipeline(pipeline_id):
    registry = _load_registry()
    if pipeline_id not in registry:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    try:
        from app import get_orchestrator
        orch = get_orchestrator()
        if orch and orch.self_host:
            result = orch.self_host.delete_deployment(pipeline_id)
            return jsonify(result), 200
    except Exception:
        pass

    del registry[pipeline_id]
    try:
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'message': f'Pipeline {pipeline_id} deleted'}), 200