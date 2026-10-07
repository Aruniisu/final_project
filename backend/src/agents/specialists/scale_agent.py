"""
ScaleAgent — Autonomous Scaling Agent
Uses scale_service as a tool.
Returns multiple field aliases so frontend can render any variant.
"""

import os
import re
import time
from typing import Dict, Any, Optional
from ..base_agent import BaseAgent


def _parse_github_url(url: str):
    """Parse GitHub URL → (owner, repo)."""
    if not url:
        return None, None
    raw = url.strip().rstrip('/')
    if raw.endswith('.git'):
        raw = raw[:-4]
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', raw)
    if m:
        return m.group(1), m.group(2)
    return None, None


class ScaleAgent(BaseAgent):
    """Autonomous scaling agent."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'ScaleAgent',
            config={
                **(config or {}),
                'role': 'scaling specialist',
                'goal': 'Scale services up/down autonomously',
                'capabilities': ['scale_service', 'list_services', 'analyze_load'],
                'max_retries': 2,
            }
        )
        self.total_scales = 0
        self.successful_scales = 0

    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        sid = context.get('sid') if context else None
        if not isinstance(input_data, dict):
            input_data = {'query': str(input_data)}

        repo_url = input_data.get('repo_url') or input_data.get('repoUrl')
        service = input_data.get('service')
        replicas = int(input_data.get('replicas', 3))

        # Parse repo
        owner, repo = _parse_github_url(repo_url or '')
        if not repo:
            q = input_data.get('query', '')
            m = re.search(r'https?://github\.com/([^/]+)/([^/]+)', q)
            if m:
                owner, repo = m.group(1), m.group(2)

        if not repo:
            return self._error_response("Need a GitHub repo URL to scale", sid)

        if not service:
            service = repo.lower().replace('_', '-')

        self.emit_log("=" * 60, "info", sid)
        self.emit_log("📈 ScaleAgent started", "info", sid)
        self.emit_log(f"   Service: {service}", "info", sid)
        self.emit_log(f"   Replicas: {replicas}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        start = time.time()
        try:
            from services.scale_service import scale_service
            self.emit_log(f"   🚀 Scaling {service} → {replicas} replicas...", "info", sid)

            result = scale_service.scale_service(
                service_name=service,
                replicas=replicas,
                repo_url=repo_url,
                action_id=None,
            )

            elapsed = time.time() - start
            self.total_scales += 1
            self.successful_scales += 1
            self.track_metric(True, elapsed)

            # ── Extract replica counts from result ──
            old = 1
            new = replicas
            if result:
                old = (
                    result.get('old_replicas')
                    or result.get('old')
                    or result.get('from')
                    or 1
                )
                new = (
                    result.get('replicas')
                    or result.get('new_replicas')
                    or result.get('new')
                    or result.get('to')
                    or replicas
                )

            # Also check action_store if available
            action_id = input_data.get('action_id')
            if action_id:
                try:
                    from services.action_store import action_store
                    action = action_store.get_action(action_id)
                    if action and action.get('result'):
                        r = action['result']
                        old = r.get('old_replicas', old)
                        new = r.get('new_replicas', new)
                except Exception:
                    pass

            response_md = (
                f"## 📈 Scale Complete\n\n"
                f"**Service:** `{service}`\n"
                f"**Replicas:** {old} → **{new}**\n"
                f"**Time:** {elapsed:.1f}s\n\n"
                f"*Scaled by ScaleAgent*"
            )
            self._emit_chat(sid, response_md)

            self.emit_log(f"   ✓ Scaled {service} to {new} replicas", "success", sid)

            # ── Return with ALL alias fields ──
            return {
                'success': True,
                'type': 'scale',
                'service': service,

                # Original field names
                'old_replicas': old,
                'new_replicas': new,

                # Frontend aliases
                'old': old,
                'new': new,
                'from': old,
                'to': new,
                'replicas': new,
                'count': new,

                'duration': f'{elapsed:.1f}s',
                'response': response_md,

                # Nested result (for /api/devops/action/scale consumers)
                'result': {
                    'service': service,
                    'old_replicas': old,
                    'new_replicas': new,
                    'old': old,
                    'new': new,
                    'from': old,
                    'to': new,
                    'replicas': new,
                    'count': new,
                },
            }
        except Exception as e:
            elapsed = time.time() - start
            self.track_metric(False, elapsed)
            self.emit_log(f"❌ Scale failed: {str(e)[:200]}", "error", sid)
            import traceback
            traceback.print_exc()
            return self._error_response(str(e), sid)

    def _emit_chat(self, sid, markdown):
        """Emit chat bubble to frontend."""
        try:
            from core.event_bus import _socketio, emit_event
            # Platform event (live logs)
            emit_event('scale:report', {
                'markdown': markdown,
                'sid': sid,
            })
            # Chat bubble
            if _socketio:
                payload = {
                    'message': markdown,
                    'source': 'ScaleAgent',
                    'type': 'scale_report',
                    'timestamp': time.strftime('%H:%M:%S'),
                }
                if sid:
                    _socketio.emit('chat_response', payload, room=sid)
                else:
                    _socketio.emit('chat_response', payload)
        except Exception:
            pass

    def _error_response(self, msg, sid=None):
        print(f"[SCALE] ERROR: {msg}", flush=True)
        self.emit_log(f"❌ Error: {msg}", "error", sid)
        response = f"## ❌ Scale Failed\n\n**Error:** {msg}"
        self._emit_chat(sid, response)
        return {'success': False, 'error': msg, 'response': response}

    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {
            **base,
            'total_scales': self.total_scales,
            'successful_scales': self.successful_scales,
            'success_rate': (
                (self.successful_scales / self.total_scales * 100)
                if self.total_scales > 0 else 0
            ),
        }


# Singleton instance (matches import style used by orchestrator)
scale_agent = ScaleAgent()