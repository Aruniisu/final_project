"""
Infrastructure Agentic AI Backend — Universal Cross-Page Manager
================================================================
Autonomous infrastructure management + Level 3 self-learning.
"""

from flask import Blueprint, request, jsonify
import psutil
import time
import threading
import subprocess
import os
import re
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict, field
from collections import deque
from typing import List

from core.process_manager import manager
from core.universal_registry import list_all_apps, get_stats as registry_stats
from core.event_bus import emit_event
from ml.feedback import log_action

infra_bp = Blueprint('infra', __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR / 'deployed_apps'

# ============================================
# GLOBAL STATE
# ============================================
METRIC_HISTORY = deque(maxlen=120)
DECISIONS = deque(maxlen=200)
EXECUTED = deque(maxlen=100)
COOLDOWNS = {}

m_cache = {'cpu_percent': 0, 'memory_percent': 0, 'disk_percent': 0}

AGENT = {
    'mode': 'assistive',
    'running': True,
    'confidence_threshold': 0.75,
    'total_decisions': 0,
    'total_actions': 0,
    'success_rate': 1.0,
    'last_tick': 0,
    'safety': {
        'max_scale': 10,
        'min_scale': 1,
        'cooldown_seconds': 60,
        'max_actions_per_hour': 30,
    },
}


@dataclass
class Decision:
    id: str
    tool: str
    args: dict
    reason: str
    confidence: float
    severity: str
    source: str
    timestamp: float
    status: str = 'pending'
    result: dict = field(default_factory=dict)


# ============================================
# PERCEIVE
# ============================================
def get_metrics() -> dict:
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\' if os.name == 'nt' else '/').percent
        net = psutil.net_io_counters()
        return {
            'cpu_percent': round(cpu, 1),
            'memory_percent': round(mem, 1),
            'disk_percent': round(disk, 1),
            'network_mbps': round((net.bytes_sent + net.bytes_recv) / 1_000_000, 2),
        }
    except Exception:
        return {'cpu_percent': 0, 'memory_percent': 0,
                'disk_percent': 0, 'network_mbps': 0}


def get_services() -> List[dict]:
    return list_all_apps()


def compute_health(services: List[dict], metrics: dict) -> dict:
    score = 100
    score -= min(25, metrics['cpu_percent'] * 0.25)
    score -= min(25, metrics['memory_percent'] * 0.25)
    score -= sum(15 for s in services if s['status'] == 'crashed')
    score = max(0, min(100, round(score)))
    if score >= 90:
        status = 'excellent'
    elif score >= 70:
        status = 'good'
    elif score >= 50:
        status = 'warning'
    else:
        status = 'critical'
    return {'score': score, 'status': status}


# ============================================
# TOOLS
# ============================================
def _detect_start_command(path: Path) -> str:
    files = {f.name.lower() for f in path.iterdir()} if path.exists() else set()
    if 'package.json' in files:
        return 'npm install && npm start'
    if 'requirements.txt' in files or 'app.py' in files or 'main.py' in files:
        for candidate in ['app.py', 'main.py', 'run.py', 'server.py']:
            if candidate in files:
                if 'requirements.txt' in files:
                    return f'pip install -r requirements.txt && python {candidate}'
                return f'python {candidate}'
        return 'python app.py'
    if 'manage.py' in files:
        return 'pip install -r requirements.txt && python manage.py runserver 0.0.0.0:$PORT'
    if 'index.html' in files:
        return 'python -m http.server $PORT'
    return 'python -m http.server $PORT'


def tool_launch_app(repo_url: str, name: str = None) -> dict:
    try:
        repo_name = (name or repo_url.rstrip('/').split('/')[-1]).replace('.git', '')
        repo_name = re.sub(r'[^a-zA-Z0-9_-]', '-', repo_name).lower()
        if not repo_name:
            return {'success': False, 'error': 'Invalid repo name'}

        target = REPO_DIR / repo_name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)

        r = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, str(target)],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            return {'success': False, 'error': f'Clone failed: {r.stderr[:200]}'}

        command = _detect_start_command(target)
        reg = manager.register_app(repo_name, str(target), command)
        if not reg.get('success'):
            return reg
        start = manager.start_app(repo_name)
        return {**start, 'name': repo_name, 'detected_command': command}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def tool_stop_app(name: str) -> dict:
    return manager.stop_app(name)


def tool_restart_app(name: str) -> dict:
    return manager.restart_app(name)


def tool_scale_app(service: str, replicas: int) -> dict:
    if replicas > AGENT['safety']['max_scale']:
        return {'success': False, 'error': f'Max scale {AGENT["safety"]["max_scale"]}'}
    if replicas < AGENT['safety']['min_scale']:
        return {'success': False, 'error': f'Min scale {AGENT["safety"]["min_scale"]}'}
    return {
        'success': True, 'service': service,
        'old_replicas': 1, 'new_replicas': replicas,
        'message': f'Scaled {service} to {replicas}',
    }


def tool_cleanup_disk() -> dict:
    try:
        registered = {a['service_name'] for a in manager.list_apps()}
        removed = 0
        for f in REPO_DIR.iterdir():
            if f.is_dir() and not f.name.startswith('_') and f.name not in registered:
                shutil.rmtree(f, ignore_errors=True)
                removed += 1
        return {'success': True, 'removed': removed,
                'message': f'Cleaned {removed} folders'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def tool_notify(message: str) -> dict:
    return {'success': True, 'message': message, 'delivered': True}


TOOLS = {
    'launch_app': {'fn': tool_launch_app, 'description': 'Clone + install + start a GitHub repo', 'args': ['repo_url'], 'risk': 'medium'},
    'stop_app': {'fn': tool_stop_app, 'description': 'Stop a running app', 'args': ['name'], 'risk': 'low'},
    'restart_app': {'fn': tool_restart_app, 'description': 'Restart an app', 'args': ['name'], 'risk': 'low'},
    'scale_app': {'fn': tool_scale_app, 'description': 'Set replica count', 'args': ['service', 'replicas'], 'risk': 'medium'},
    'cleanup_disk': {'fn': tool_cleanup_disk, 'description': 'Remove unused deployment folders', 'args': [], 'risk': 'low'},
    'notify': {'fn': tool_notify, 'description': 'Send notification', 'args': ['message'], 'risk': 'low'},
}


# ============================================
# REASON — with cooldowns
# ============================================
def reason(services: List[dict], metrics: dict, history: list) -> List[Decision]:
    out = []
    now = time.time()

    # High CPU (5 min cooldown)
    if metrics['cpu_percent'] > 80:
        key = 'cpu_alert'
        if now - COOLDOWNS.get(key, 0) > 300:
            COOLDOWNS[key] = now
            conf = min(0.95, 0.6 + (metrics['cpu_percent'] - 80) / 100)
            out.append(Decision(
                id=f"dec-{int(now)}-cpu",
                tool='notify',
                args={'message': f"CPU {metrics['cpu_percent']}% — investigate"},
                reason=f"CPU {metrics['cpu_percent']}% exceeds 80%",
                confidence=round(conf, 2),
                severity='critical' if metrics['cpu_percent'] > 90 else 'warning',
                source='rule', timestamp=now,
            ))

    # Crashed services
    for s in services:
        if s['status'] == 'crashed':
            if now - COOLDOWNS.get(s['service_name'], 0) < AGENT['safety']['cooldown_seconds']:
                continue
            out.append(Decision(
                id=f"dec-{int(now)}-down-{s['service_name']}",
                tool='restart_app', args={'name': s['service_name']},
                reason=f"{s['service_name']} crashed — auto-restart",
                confidence=0.9, severity='critical', source='rule', timestamp=now,
            ))

    # High Memory (5 min cooldown)
    if metrics['memory_percent'] > 85:
        key = 'mem_alert'
        if now - COOLDOWNS.get(key, 0) > 300:
            COOLDOWNS[key] = now
            out.append(Decision(
                id=f"dec-{int(now)}-mem",
                tool='notify',
                args={'message': f"Memory {metrics['memory_percent']}%"},
                reason=f"Memory {metrics['memory_percent']}%",
                confidence=0.75, severity='warning', source='rule', timestamp=now,
            ))

    # High Disk (10 min cooldown)
    if metrics['disk_percent'] > 85:
        key = 'disk_alert'
        if now - COOLDOWNS.get(key, 0) > 600:
            COOLDOWNS[key] = now
            out.append(Decision(
                id=f"dec-{int(now)}-disk",
                tool='cleanup_disk', args={},
                reason=f"Disk {metrics['disk_percent']}%",
                confidence=0.8, severity='warning', source='rule', timestamp=now,
            ))

    # CPU trend
    if len(history) >= 10:
        recent = [h['cpu'] for h in history[-10:]]
        if recent[-1] > recent[0] * 1.4 and recent[-1] > 60:
            key = 'trend_alert'
            if now - COOLDOWNS.get(key, 0) > 600:
                COOLDOWNS[key] = now
                out.append(Decision(
                    id=f"dec-{int(now)}-trend",
                    tool='notify',
                    args={'message': f"CPU trending up: {recent[0]:.0f}% → {recent[-1]:.0f}%"},
                    reason='Rapid CPU growth',
                    confidence=0.65, severity='info', source='rule', timestamp=now,
                ))
    return out


# ============================================
# ACT
# ============================================
def execute(decision: Decision) -> dict:
    tool = TOOLS.get(decision.tool)
    if not tool:
        return {'success': False, 'error': 'Unknown tool'}

    svc = decision.args.get('name') or decision.args.get('service')
    if svc and decision.source != 'user':
        if time.time() - COOLDOWNS.get(svc, 0) < AGENT['safety']['cooldown_seconds']:
            return {'success': False, 'error': 'Cooldown active'}

    try:
        result = tool['fn'](**decision.args)
    except Exception as e:
        result = {'success': False, 'error': str(e)}

    if svc and result.get('success'):
        COOLDOWNS[svc] = time.time()

    AGENT['total_actions'] += 1
    decision.result = result
    decision.status = 'executed' if result.get('success') else 'failed'
    EXECUTED.append(decision)

    emit_event('agent:action', {
        'tool': decision.tool,
        'args': decision.args,
        'success': result.get('success', False),
        'decision_id': decision.id,
        'severity': decision.severity,
    })

    # Log feedback for auto-training
    try:
        svcs = get_services()
        feats = [
            m_cache.get('cpu_percent', 0),
            m_cache.get('memory_percent', 0),
            m_cache.get('disk_percent', 0),
            len(svcs),
            len([s for s in svcs if s.get('status') == 'running']),
            len([s for s in svcs if s.get('status') == 'crashed']),
            int((time.time() / 3600) % 24),
            len(EXECUTED),
        ]
        log_action(
            tool=decision.tool,
            features=feats,
            success=result.get('success', False),
            confidence=decision.confidence or 0.5,
        )
    except Exception as e:
        print(f"⚠️  Feedback log: {e}")

    print(f"⚡ Executed: {decision.tool} → {result.get('success')}")
    return result


# ============================================
# HELPER — Chat commands auto-execute
# ============================================
def _handle_user_decision(decision: Decision) -> bool:
    """Chat commands: auto-execute in autonomous mode."""
    if AGENT['mode'] == 'autonomous':
        result = execute(decision)
        DECISIONS.append(decision)
        return result.get('success', False)
    else:
        DECISIONS.append(decision)
        return False


# ============================================
# LOOP
# ============================================
def loop():
    print("🤖 [Agent] Loop started (universal mode)")
    while AGENT['running']:
        try:
            m = get_metrics()
            m_cache.update(m)

            METRIC_HISTORY.append({
                'cpu': m['cpu_percent'], 'mem': m['memory_percent'],
                'ts': time.time(),
            })

            if AGENT['mode'] == 'off':
                time.sleep(5)
                continue

            services = get_services()
            for d in reason(services, m, list(METRIC_HISTORY)):
                AGENT['total_decisions'] += 1
                if d.confidence < AGENT['confidence_threshold']:
                    d.status = 'suggested'
                    DECISIONS.append(d)
                    continue
                if AGENT['mode'] == 'autonomous':
                    execute(d)
                    DECISIONS.append(d)
                else:
                    d.status = 'pending'
                    DECISIONS.append(d)

            if EXECUTED:
                recent = list(EXECUTED)[-20:]
                AGENT['success_rate'] = round(
                    sum(1 for a in recent if a.status == 'executed') / len(recent), 2
                )
            AGENT['last_tick'] = time.time()
        except Exception as e:
            print(f"⚠️  [Agent] Loop error: {e}")
        time.sleep(30)


_thread = None

def start_agent():
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=loop, daemon=True)
        _thread.start()


# ============================================
# STATE
# ============================================
def agent_state_data() -> dict:
    return {
        'mode': AGENT['mode'],
        'running': AGENT['running'],
        'confidence_threshold': AGENT['confidence_threshold'],
        'total_decisions': AGENT['total_decisions'],
        'total_actions': AGENT['total_actions'],
        'success_rate': AGENT['success_rate'],
        'last_tick': AGENT['last_tick'],
        'pending_count': sum(1 for d in DECISIONS if d.status == 'pending'),
        'tools_count': len(TOOLS),
        'safety': AGENT['safety'],
    }


# ============================================
# ROUTES
# ============================================
@infra_bp.route('/unified', methods=['GET'])
def unified():
    start_agent()
    services = get_services()
    m = get_metrics()
    health = compute_health(services, m)
    avg_cpu = round(sum(s['cpu_percent'] for s in services) / max(1, len(services)), 1)
    avg_mem = round(sum(s['memory_percent'] for s in services) / max(1, len(services)), 1)
    reg = registry_stats()

    return jsonify({
        'success': True,
        'services': services,
        'stats': {
            'total_services': reg['total'],
            'total_replicas': reg['total'],
            'avg_cpu': avg_cpu,
            'avg_memory': avg_mem,
            'total_deployments': 0,
            'total_monitors': 0,
            'by_source': reg.get('by_source', {}),
        },
        'health': health,
        'high_performance': {
            'cpu_percent': m['cpu_percent'],
            'memory_percent': m['memory_percent'],
            'disk_percent': m['disk_percent'],
            'network_in_mbps': m['network_mbps'],
        },
        'agent': agent_state_data(),
    })


@infra_bp.route('/insights', methods=['GET'])
def insights():
    return jsonify({'insights': [asdict(d) for d in list(DECISIONS)[-20:]]})


@infra_bp.route('/predictions', methods=['GET'])
def predictions():
    preds = []
    if len(METRIC_HISTORY) >= 5:
        cpu = [h['cpu'] for h in METRIC_HISTORY]
        slope = (cpu[-1] - cpu[-5]) / 5
        future = cpu[-1] + slope * 30
        if future > 85:
            preds.append({
                'id': f'pred-{int(time.time())}',
                'severity': 'warning', 'service': 'System',
                'prediction': f'CPU will reach {min(100, future):.0f}%',
                'timeframe': 'in 30 seconds',
            })
    return jsonify({'predictions': preds})


@infra_bp.route('/cost-savings', methods=['GET'])
def cost_savings():
    out = []
    for s in get_services():
        if s['status'] == 'running' and s['cpu_percent'] < 5 and s['memory_percent'] < 20:
            out.append({
                'id': f'cost-{s["service_name"]}',
                'service': s['service_name'],
                'suggestion': f"Idle — CPU {s['cpu_percent']}%",
                'estimated_savings': '$2.50/day',
            })
    return jsonify({'cost_savings': out})


@infra_bp.route('/action-log', methods=['GET'])
def action_log():
    return jsonify({'actions': [asdict(a) for a in list(EXECUTED)[-50:]]})


@infra_bp.route('/apply-insight', methods=['POST'])
def apply_insight():
    data = request.get_json() or {}
    did = data.get('insight_id')
    for d in DECISIONS:
        if d.id == did:
            r = execute(d)
            return jsonify({'success': True, 'action': asdict(d), 'result': r})
    return jsonify({'success': False, 'error': 'Not found'})


@infra_bp.route('/dismiss-insight', methods=['POST'])
def dismiss_insight():
    data = request.get_json() or {}
    did = data.get('insight_id')
    for d in DECISIONS:
        if d.id == did:
            d.status = 'rejected'
    return jsonify({'success': True})


@infra_bp.route('/agent/state', methods=['GET'])
def agent_state():
    return jsonify(agent_state_data())


@infra_bp.route('/agent/mode', methods=['POST'])
def set_mode():
    """Switch mode + auto-execute pending on autonomous."""
    data = request.get_json() or {}
    mode = data.get('mode', 'assistive')
    if mode not in ('off', 'assistive', 'autonomous'):
        return jsonify({'success': False, 'error': 'Invalid mode'})
    AGENT['mode'] = mode
    print(f"🎛️  Agent mode → {mode}")

    # ⭐ Auto-execute pending decisions when switching to autonomous
    if mode == 'autonomous':
        pending = [d for d in DECISIONS if d.status == 'pending']
        executed = 0
        for d in pending:
            try:
                execute(d)
                executed += 1
            except Exception as e:
                print(f"⚠️  Auto-execute failed: {e}")
        if executed:
            print(f"⚡ Auto-executed {executed} pending decisions")

    emit_event('agent:mode_changed', {'mode': mode})
    return jsonify({'success': True, 'mode': mode})


@infra_bp.route('/agent/confidence', methods=['POST'])
def set_conf():
    data = request.get_json() or {}
    t = float(data.get('threshold', 0.75))
    AGENT['confidence_threshold'] = max(0.0, min(1.0, t))
    return jsonify({'success': True, 'threshold': AGENT['confidence_threshold']})


@infra_bp.route('/agent/decisions', methods=['GET'])
def get_decisions():
    limit = int(request.args.get('limit', 30))
    return jsonify({'decisions': [asdict(d) for d in list(DECISIONS)[-limit:]]})


@infra_bp.route('/agent/execute', methods=['POST'])
def agent_execute():
    data = request.get_json() or {}
    did = data.get('decision_id')
    for d in DECISIONS:
        if d.id == did:
            r = execute(d)
            return jsonify({'success': True, 'result': r, 'decision': asdict(d)})
    return jsonify({'success': False, 'error': 'Not found'})


@infra_bp.route('/agent/tools', methods=['GET'])
def agent_tools():
    return jsonify({
        'tools': [
            {'name': k, 'description': v['description'],
             'args': v['args'], 'risk': v['risk']}
            for k, v in TOOLS.items()
        ]
    })


# ============================================
# CHAT
# ============================================
@infra_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'success': False, 'error': 'Empty'})

    lower = msg.lower()
    services = get_services()
    m = get_metrics()

    # ── Mode controls ──
    if 'autonomous' in lower:
        AGENT['mode'] = 'autonomous'
        pending = [d for d in DECISIONS if d.status == 'pending']
        for d in pending:
            try:
                execute(d)
            except Exception:
                pass
        emit_event('agent:mode_changed', {'mode': 'autonomous'})
        return jsonify({'success': True, 'message': '✅ Agent → **AUTONOMOUS**'})
    if 'assistive' in lower or 'approval' in lower:
        AGENT['mode'] = 'assistive'
        emit_event('agent:mode_changed', {'mode': 'assistive'})
        return jsonify({'success': True, 'message': '✅ Agent → **ASSISTIVE**'})
    if lower.strip() in ('off', 'stop agent', 'pause'):
        AGENT['mode'] = 'off'
        emit_event('agent:mode_changed', {'mode': 'off'})
        return jsonify({'success': True, 'message': '⏸️ Agent paused.'})

    # ── LAUNCH ──
    launch_match = re.search(
        r'(?:launch|run|start|deploy|open)\s+(https?://github\.com/\S+)', msg, re.I
    )
    if launch_match:
        repo = launch_match.group(1)
        d = Decision(
            id=f"chat-{int(time.time())}",
            tool='launch_app', args={'repo_url': repo},
            reason=f'User: {msg}',
            confidence=0.95, severity='info', source='user',
            timestamp=time.time(), status='pending',
        )
        auto = _handle_user_decision(d)
        suffix = ' (auto-executed ✅)' if auto else ''
        return jsonify({
            'success': True,
            'message': f"🚀 Ready to **launch** `{repo.split('/')[-1]}`{suffix}.",
            'decision': asdict(d),
        })

    # ── STOP ──
    stop_match = re.search(r'(?:stop|kill|terminate)\s+([a-z0-9_-]+)', msg, re.I)
    if stop_match:
        name = stop_match.group(1)
        d = Decision(
            id=f"chat-{int(time.time())}",
            tool='stop_app', args={'name': name},
            reason=f'User: {msg}', confidence=0.9, severity='info',
            source='user', timestamp=time.time(), status='pending',
        )
        auto = _handle_user_decision(d)
        suffix = ' (auto-executed ✅)' if auto else ''
        return jsonify({'success': True,
            'message': f"🛑 **stop {name}**{suffix}.", 'decision': asdict(d)})

    # ── RESTART ──
    restart_match = re.search(r'(?:restart|reboot|reload)\s+([a-z0-9_-]+)', msg, re.I)
    if restart_match:
        name = restart_match.group(1)
        d = Decision(
            id=f"chat-{int(time.time())}",
            tool='restart_app', args={'name': name},
            reason=f'User: {msg}', confidence=0.9, severity='info',
            source='user', timestamp=time.time(), status='pending',
        )
        auto = _handle_user_decision(d)
        suffix = ' (auto-executed ✅)' if auto else ''
        return jsonify({'success': True,
            'message': f"🔄 **restart {name}**{suffix}.", 'decision': asdict(d)})

    # ── SCALE ──
    scale_match = re.search(
        r'(?:scale)\s+([a-z0-9_-]+)\s+(?:to\s+)?(\d+)', msg, re.I
    )
    if scale_match:
        svc = scale_match.group(1)
        reps = int(scale_match.group(2))
        d = Decision(
            id=f"chat-{int(time.time())}",
            tool='scale_app',
            args={'service': svc, 'replicas': reps},
            reason=f'User: {msg}',
            confidence=0.9, severity='info', source='user',
            timestamp=time.time(), status='pending',
        )
        auto = _handle_user_decision(d)
        suffix = ' (auto-executed ✅)' if auto else ''
        return jsonify({
            'success': True,
            'message': f"📈 **scale {svc} → {reps}**{suffix}.",
            'decision': asdict(d),
        })

    # ── CLEANUP ──
    if 'cleanup' in lower or 'clean up' in lower or 'clean disk' in lower:
        d = Decision(
            id=f"chat-{int(time.time())}",
            tool='cleanup_disk',
            args={},
            reason=f'User: {msg}',
            confidence=0.9, severity='info', source='user',
            timestamp=time.time(), status='pending',
        )
        auto = _handle_user_decision(d)
        suffix = ' (auto-executed ✅)' if auto else ''
        return jsonify({
            'success': True,
            'message': f"🧹 **cleanup disk**{suffix}.",
            'decision': asdict(d),
        })

    # ── STATUS ──
    if any(w in lower for w in ['status', 'health', 'cpu', 'list', 'apps', 'services']):
        lines = [f"**System** — CPU {m['cpu_percent']}%, "
                 f"Mem {m['memory_percent']}%, Disk {m['disk_percent']}%"]
        if services:
            lines.append(f"\n**Apps ({len(services)}):**")
            for s in services[:8]:
                dot = '🟢' if s['status'] == 'running' else '🔴'
                src = 'P' if s.get('source') == 'process-manager' else 'S'
                lines.append(f"{dot} [{src}] `{s['service_name']}` — "
                             f"{s['status']} · CPU {s['cpu_percent']}%")
        else:
            lines.append("\n_No apps running. Try:_ "
                         "`launch https://github.com/user/repo`")
        return jsonify({'success': True, 'message': '\n'.join(lines)})

    # ── FALLBACK ──
    return jsonify({
        'success': True,
        'message': (
            "**I can:**\n"
            "- `launch <github-url>`\n"
            "- `restart <name>` / `stop <name>`\n"
            "- `scale <name> to <n>`\n"
            "- `cleanup disk`\n"
            "- `status`\n"
            "- `autonomous` / `assistive`"
        ),
    })


@infra_bp.route('/events', methods=['GET'])
def events():
    return jsonify({'events': [asdict(a) for a in list(EXECUTED)[-20:]]})


# ============================================
# CROSS-PAGE REACTIONS
# ============================================
@infra_bp.route('/react', methods=['POST'])
def react_to_event():
    data = request.get_json() or {}
    event_type = data.get('type', '')
    event_data = data.get('data', {})

    print(f"📥 [Infra Agent] React to: {event_type}")
    actions_taken = []

    if event_type == 'pipeline:deployed':
        actions_taken.append(f"Now monitoring: {event_data.get('name', 'unknown')}")

    elif event_type == 'pipeline:failed':
        d = Decision(
            id=f"evt-{int(time.time())}", tool='notify',
            args={'message': f"Pipeline failed: {event_data.get('repo', 'unknown')}"},
            reason='Pipeline failure', confidence=0.95, severity='critical',
            source='event', timestamp=time.time(), status='pending',
        )
        DECISIONS.append(d)
        actions_taken.append('Queued: notify failure')

    elif event_type == 'assistant:launched':
        actions_taken.append(f"Tracking: {event_data.get('name', 'app')}")

    elif event_type == 'monitoring:alert':
        alert = event_data.get('alert', {})
        severity = alert.get('severity', 'info')
        service = alert.get('service', '') or alert.get('name', '')
        if severity in ('critical', 'high') and service:
            d = Decision(
                id=f"evt-{int(time.time())}", tool='restart_app',
                args={'name': service},
                reason=f"Monitoring alert ({severity}) on {service}",
                confidence=0.85, severity='critical', source='event',
                timestamp=time.time(), status='pending',
            )
            DECISIONS.append(d)
            actions_taken.append(f'Queued restart: {service}')

    elif event_type == 'training:completed':
        d = Decision(
            id=f"evt-{int(time.time())}", tool='cleanup_disk', args={},
            reason='Training done — cleanup',
            confidence=0.7, severity='info', source='event',
            timestamp=time.time(), status='pending',
        )
        DECISIONS.append(d)
        actions_taken.append('Queued: cleanup disk')

    if AGENT['mode'] == 'autonomous':
        pending_evt = [x for x in DECISIONS
                       if x.status == 'pending' and x.source == 'event']
        for d in pending_evt:
            try:
                execute(d)
                actions_taken.append(f'Executed: {d.tool}')
            except Exception as e:
                actions_taken.append(f'Failed: {e}')

    emit_event('agent:reaction', {
        'trigger': event_type,
        'actions_taken': actions_taken,
        'mode': AGENT['mode'],
    })

    return jsonify({
        'success': True, 'event': event_type,
        'actions_taken': actions_taken,
        'agent_mode': AGENT['mode'],
    })