"""
MonitorAgent - Agentic Monitoring & Observability
Real-time monitoring, health checks, alerting with LLM analysis.
Emits chat responses back to UI.
Integrated with monitor_service for dashboard persistence.
"""

import os
import time
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..base_agent import BaseAgent


class MonitorAgent(BaseAgent):
    """Agentic monitoring agent with chat responses + dashboard integration."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'MonitorAgent',
            config={
                **(config or {}),
                'role': 'monitoring specialist',
                'goal': 'Monitor applications and detect issues proactively',
                'capabilities': [
                    'health_check',
                    'collect_metrics',
                    'analyze_anomalies',
                    'generate_alerts',
                ],
            }
        )
        self.total_checks = 0
        self.total_alerts = 0

    # ============================================
    # Main Entry
    # ============================================
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        sid = context.get('sid') if context else None
        action = input_data.get('action', 'check') if isinstance(input_data, dict) else 'check'

        self.emit_log("=" * 60, "info", sid)
        self.emit_log("MonitorAgent started", "info", sid)
        self.emit_log(f"Action: {action}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        start_time = time.time()

        try:
            if action == 'check':
                return self._health_check(input_data, context, sid, start_time)
            elif action == 'monitor':
                return self._monitor_url(input_data, context, sid, start_time)
            elif action == 'analyze':
                return self._analyze_metrics(input_data, context, sid, start_time)
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}

        except Exception as e:
            elapsed = time.time() - start_time
            self.track_metric(False, elapsed)
            self.emit_log(f"Fatal error: {str(e)[:200]}", "error", sid)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    # ============================================
    # Health Check (with dashboard integration)
    # ============================================
    def _health_check(self, input_data: Dict, context: Dict, sid: Optional[str], start_time: float) -> Dict:
        urls = input_data.get('urls', [])
        if isinstance(input_data.get('url'), str):
            urls = [input_data['url']]

        if not urls:
            return {'success': False, 'error': 'No URLs provided'}

        project_name = context.get('project_name', 'Unknown') if context else 'Unknown'
        repo_url = context.get('repo_url', '') if context else ''

        self.emit_log(f"Checking {len(urls)} URL(s)", "info", sid)

        results = []
        all_healthy = True
        dashboard_monitors = []

        for url in urls:
            self.emit_log("", "info", sid)
            self.emit_log(f"Checking: {url}", "info", sid)

            # Step 1: Immediate check for chat response
            result = self._check_single_url(url, sid)
            results.append(result)

            if not result.get('healthy'):
                all_healthy = False

            # Step 2: Register with monitor_service (for continuous monitoring + dashboard)
            try:
                from services.monitor_service import monitor_service

                # Check if monitor already exists for this URL
                existing = None
                for m in monitor_service.list_monitors():
                    if m.get('url') == url:
                        existing = m
                        break

                if existing:
                    # Already registered — just log
                    dashboard_monitors.append(existing)
                    self.emit_log(
                        f"   Dashboard: monitor exists ({existing.get('id', 'N/A')[:16]})",
                        "info", sid
                    )
                else:
                    # Register new monitor (starts background thread)
                    monitor = monitor_service.start_monitor(
                        url=url,
                        interval=30,
                        repo_url=repo_url,
                        project_name=project_name,
                    )
                    dashboard_monitors.append(monitor)
                    self.emit_log(
                        f"   Dashboard: new monitor started ({monitor.get('id', 'N/A')[:16]})",
                        "success", sid
                    )
                    self.emit_log(
                        f"   Background polling every 30s",
                        "info", sid
                    )
            except Exception as e:
                self.emit_log(f"   Dashboard registration failed: {str(e)[:120]}", "warning", sid)
                import traceback
                traceback.print_exc()

            self.total_checks += 1

        elapsed = time.time() - start_time
        self.track_metric(all_healthy, elapsed)

        # LLM analysis if there are issues
        analysis = None
        if not all_healthy:
            self.emit_log("", "info", sid)
            self.emit_log("Analyzing issues (LLM)", "info", sid)
            analysis = self._analyze_issues(results, sid)
            if analysis:
                self.emit_log(f"{analysis.get('summary', 'N/A')}", "info", sid)
                self.total_alerts += 1

        # Build response
        healthy_count = sum(1 for r in results if r.get('healthy'))
        response_md = self._build_monitor_response(results, analysis, dashboard_monitors)

        # Emit to chat
        self._emit_chat(sid, response_md)

        return {
            'success': True,
            'type': 'monitor',
            'status': 'completed',
            'healthy': all_healthy,
            'healthy_count': healthy_count,
            'total_count': len(results),
            'results': results,
            'analysis': analysis,
            'dashboard_monitors': [
                {
                    'id': m.get('id'),
                    'url': m.get('url'),
                    'status': m.get('status'),
                    'interval': m.get('interval'),
                }
                for m in dashboard_monitors
            ],
            'duration': f'{elapsed:.2f}s',
            'response': response_md,
        }

    def _check_single_url(self, url: str, sid: Optional[str] = None) -> Dict:
        """Check one URL."""
        try:
            start = time.time()
            response = requests.get(url, timeout=10, allow_redirects=True)
            elapsed = (time.time() - start) * 1000  # ms

            healthy = response.status_code < 500

            self.emit_log(
                f"   Status: {response.status_code} | Time: {elapsed:.0f}ms",
                "success" if healthy else "warning",
                sid
            )

            return {
                'url': url,
                'status_code': response.status_code,
                'response_time_ms': round(elapsed, 2),
                'healthy': healthy,
                'content_length': len(response.content),
            }
        except requests.Timeout:
            self.emit_log(f"   Timeout", "error", sid)
            return {'url': url, 'healthy': False, 'error': 'Timeout'}
        except requests.ConnectionError:
            self.emit_log(f"   Connection error", "error", sid)
            return {'url': url, 'healthy': False, 'error': 'Connection error'}
        except Exception as e:
            self.emit_log(f"   {str(e)[:100]}", "error", sid)
            return {'url': url, 'healthy': False, 'error': str(e)}

    # ============================================
    # Monitor URL (continuous — uses monitor_service)
    # ============================================
    def _monitor_url(self, input_data: Dict, context: Dict, sid: Optional[str], start_time: float) -> Dict:
        """Register a continuous monitor in monitor_service (background thread)."""
        url = input_data.get('url')
        interval = input_data.get('interval', 30)
        project_name = context.get('project_name', 'Unknown') if context else 'Unknown'
        repo_url = context.get('repo_url', '') if context else ''

        if not url:
            return {'success': False, 'error': 'No URL provided'}

        self.emit_log(f"Registering continuous monitor: {url}", "info", sid)

        try:
            from services.monitor_service import monitor_service

            # Check if monitor already exists
            existing = None
            for m in monitor_service.list_monitors():
                if m.get('url') == url:
                    existing = m
                    break

            if existing:
                monitor = existing
                self.emit_log(
                    f"Monitor already exists: {monitor.get('id', 'N/A')[:16]}",
                    "info", sid
                )
            else:
                monitor = monitor_service.start_monitor(
                    url=url,
                    interval=interval,
                    repo_url=repo_url,
                    project_name=project_name,
                )
                self.emit_log(
                    f"Monitor started: {monitor.get('id', 'N/A')[:16]}",
                    "success", sid
                )

            elapsed = time.time() - start_time
            self.track_metric(True, elapsed)

            response_md = (
                f"## Monitoring Started\n\n"
                f"**URL:** {url}\n"
                f"**Interval:** every {interval}s\n"
                f"**Monitor ID:** `{monitor.get('id', 'N/A')[:16]}`\n"
                f"**Status:** {monitor.get('status', 'running')}\n\n"
                f"View live data in the **Monitoring Dashboard**."
            )
            self._emit_chat(sid, response_md)

            return {
                'success': True,
                'type': 'monitor',
                'status': 'started',
                'monitor': monitor,
                'duration': f'{elapsed:.2f}s',
                'response': response_md,
            }

        except Exception as e:
            self.emit_log(f"Monitor registration failed: {str(e)[:150]}", "error", sid)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    # ============================================
    # LLM Analysis
    # ============================================
    def _analyze_issues(self, results: List[Dict], sid: Optional[str] = None) -> Optional[Dict]:
        """Use LLM to analyze monitoring issues."""
        failing = [r for r in results if not r.get('healthy')]
        if not failing:
            return None

        prompt = f"""Analyze these monitoring failures and provide insights:

{json.dumps(failing, indent=2, default=str)[:2000]}

Respond ONLY with valid JSON:
{{
  "severity": "critical|high|medium|low",
  "summary": "Brief 1-sentence summary of the issue",
  "root_cause": "Likely root cause",
  "recommendation": "What to do",
  "confidence": 0.0-1.0
}}"""

        response = self.call_llm(prompt, expect_json=True)
        if not response:
            return None

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def _analyze_metrics(self, input_data: Dict, context: Dict, sid: Optional[str], start_time: float) -> Dict:
        """Analyze provided metrics."""
        metrics = input_data.get('metrics', {})
        if not metrics:
            return {'success': False, 'error': 'No metrics provided'}

        prompt = f"""Analyze these system metrics:

{json.dumps(metrics, indent=2, default=str)[:2000]}

Respond ONLY with valid JSON:
{{
  "status": "healthy|warning|critical",
  "summary": "Brief summary",
  "concerns": ["concern1", "concern2"],
  "recommendation": "What to do"
}}"""

        response = self.call_llm(prompt, expect_json=True)
        try:
            analysis = json.loads(response) if response else {}
        except json.JSONDecodeError:
            analysis = {}

        elapsed = time.time() - start_time
        self.track_metric(True, elapsed)

        return {
            'success': True,
            'type': 'analysis',
            'metrics': metrics,
            'analysis': analysis,
            'duration': f'{elapsed:.2f}s',
        }

    # ============================================
    # Build response
    # ============================================
    def _build_monitor_response(self, results: List[Dict], analysis: Optional[Dict],
                                dashboard_monitors: Optional[List[Dict]] = None) -> str:
        parts = ["## Monitoring Report\n"]

        for r in results:
            status = "OK" if r.get('healthy') else "FAIL"
            parts.append(f"[{status}] **{r['url']}**")
            if r.get('status_code'):
                parts.append(f"   - Status: `{r['status_code']}`")
            if r.get('response_time_ms'):
                parts.append(f"   - Response: `{r['response_time_ms']}ms`")
            if r.get('error'):
                parts.append(f"   - Error: `{r['error']}`")
            parts.append("")

        if dashboard_monitors:
            parts.append("### Dashboard")
            parts.append(f"{len(dashboard_monitors)} monitor(s) registered for continuous tracking:")
            for m in dashboard_monitors:
                parts.append(f"- `{m.get('id', 'N/A')[:16]}` — {m.get('url')} (every {m.get('interval', 30)}s)")
            parts.append("")
            parts.append("*View live data in Monitoring Dashboard*")
            parts.append("")

        if analysis:
            parts.append("### Analysis")
            parts.append(f"**Severity:** {analysis.get('severity', 'N/A')}")
            parts.append(f"**Summary:** {analysis.get('summary', 'N/A')}")
            parts.append(f"**Root Cause:** {analysis.get('root_cause', 'N/A')}")
            parts.append(f"**Recommendation:** {analysis.get('recommendation', 'N/A')}")
            parts.append("")

        parts.append("*Monitored by MonitorAgent*")
        return '\n'.join(parts)

    # ============================================
    # Emit chat response
    # ============================================
    def _emit_chat(self, sid: Optional[str], markdown: str):
        """Emit chat message to frontend."""
        try:
            from core.event_bus import emit_event, _socketio

            # Platform event (Live Logs)
            emit_event('monitor:report', {
                'markdown': markdown,
                'sid': sid,
            })

            # Chat bubble
            if _socketio:
                payload = {
                    'message': markdown,
                    'source': 'MonitorAgent',
                    'type': 'monitor_report',
                    'timestamp': time.strftime('%H:%M:%S'),
                }
                if sid:
                    _socketio.emit('chat_response', payload, room=sid)
                else:
                    _socketio.emit('chat_response', payload)
        except Exception:
            pass

    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {
            **base,
            'total_checks': self.total_checks,
            'total_alerts': self.total_alerts,
        }