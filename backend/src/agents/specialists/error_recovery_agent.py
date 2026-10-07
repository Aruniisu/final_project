"""
ErrorRecoveryAgent — Universal Error Handler
=============================================
Wraps ANY agent action with universal recovery logic.

Use cases:
- Any agent fails → analyze → fix via HealerAgent → retry
- Workflow orchestration with fallback
- Universal error handler for the whole system

Features:
- wrap_callable(action_fn, action_name) → executes with retry + heal
- Multi-attempt recovery
- Delegates fixes to HealerAgent
- Structured recovery history
"""

import time
import traceback
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from ..base_agent import BaseAgent


class ErrorRecoveryAgent(BaseAgent):
    """
    Universal error recovery + retry orchestrator.

    Different from AutoFixWorkflow:
    - This is an AGENT (can be called from orchestrator like any other agent)
    - Has memory + metrics
    - Can be registered in the main orchestrator
    - Provides both `process()` (agent-style) and `wrap_callable()` (utility-style)
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'ErrorRecoveryAgent',
            config={
                **(config or {}),
                'role': 'universal error recovery orchestrator',
                'goal': 'Recover from any agent failure via retry + HealerAgent delegation',
                'capabilities': [
                    'wrap_action',
                    'retry_with_heal',
                    'delegate_to_healer',
                    'track_recovery',
                ],
                'max_retries': 3,
            }
        )
        self.total_recoveries = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.recovery_history: List[Dict] = []

    # ============================================
    # Main Entry Point (agent-style)
    # ============================================
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """
        Agent-style entry point.

        Usage from orchestrator:
            recovery_agent.process({
                'action_fn': lambda: some_agent.process(...),
                'action_name': 'deploy_repo_x',
                'repo_url': 'https://github.com/user/repo',
                'error_logs': '...',
            }, context)
        """
        sid = context.get('sid') if context else None

        if not isinstance(input_data, dict):
            return {'success': False, 'error': 'Input must be a dict'}

        action_fn = input_data.get('action_fn')
        action_name = input_data.get('action_name', 'unknown_action')
        repo_url = input_data.get('repo_url')
        error_logs = input_data.get('error_logs', '')
        max_attempts = input_data.get('max_attempts', 3)

        self.emit_log("=" * 60, "info", sid)
        self.emit_log("🩹 ErrorRecoveryAgent started", "info", sid)
        self.emit_log(f"   Action: {action_name}", "info", sid)
        self.emit_log(f"   Repo: {repo_url or 'N/A'}", "info", sid)
        self.emit_log(f"   Max attempts: {max_attempts}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        if not callable(action_fn):
            return {
                'success': False,
                'error': 'action_fn must be a callable returning a dict',
            }

        # Delegate to wrap_callable
        return self.wrap_callable(
            action_fn=action_fn,
            action_name=action_name,
            repo_url=repo_url,
            error_logs=error_logs,
            max_attempts=max_attempts,
            sid=sid,
            context=context,
        )

    # ============================================
    # Universal Wrapper
    # ============================================
    def wrap_callable(
        self,
        action_fn: Callable,
        action_name: str,
        repo_url: Optional[str] = None,
        error_logs: str = '',
        max_attempts: int = 3,
        sid: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute ANY callable with retry + auto-heal.

        Args:
            action_fn: Callable() -> Dict (must return dict with 'success' key)
            action_name: Human-readable action name
            repo_url: GitHub repo URL (for healing)
            error_logs: Initial error logs (optional)
            max_attempts: Max retry attempts
            sid: Socket session ID
            context: Additional context for healer

        Returns:
            Final result dict
        """
        context = context or {}
        last_error = None
        start_time = time.time()

        self.total_recoveries += 1

        for attempt in range(1, max_attempts + 1):
            self.emit_log("", "info", sid)
            self.emit_log(f"▶️  [{action_name}] Attempt {attempt}/{max_attempts}", "info", sid)

            attempt_start = time.time()

            try:
                result = action_fn()
                elapsed = time.time() - attempt_start

                if isinstance(result, dict) and result.get('success'):
                    self.emit_log(
                        f"✅ [{action_name}] Succeeded on attempt {attempt}",
                        "success", sid
                    )
                    self.successful_recoveries += 1

                    self.recovery_history.append({
                        'action': action_name,
                        'attempts': attempt,
                        'success': True,
                        'elapsed': elapsed,
                        'timestamp': datetime.now().isoformat(),
                    })

                    # Add recovery metadata
                    result['recovery'] = {
                        'attempts': attempt,
                        'auto_fixes_applied': attempt - 1,
                        'total_elapsed': time.time() - start_time,
                    }

                    return result

                # Failed but no exception
                last_error = (
                    result.get('error', 'Unknown error')
                    if isinstance(result, dict)
                    else str(result)
                )
                self.emit_log(
                    f"❌ [{action_name}] Attempt {attempt} failed: {last_error[:200]}",
                    "error", sid
                )

            except Exception as e:
                elapsed = time.time() - attempt_start
                last_error = str(e)
                self.emit_log(
                    f"❌ [{action_name}] Attempt {attempt} exception: {last_error[:200]}",
                    "error", sid
                )
                traceback.print_exc()

            # Max attempts?
            if attempt >= max_attempts:
                self.emit_log("⚠️ Max attempts reached — giving up", "error", sid)
                break

            # Try to heal
            if not repo_url:
                self.emit_log("⚠️ No repo_url — cannot delegate to healer", "warning", sid)
                break

            self.emit_log("", "info", sid)
            self.emit_log("🩺 Delegating to HealerAgent...", "info", sid)

            fix_result = self._delegate_to_healer(
                action_name=action_name,
                error=last_error,
                repo_url=repo_url,
                error_logs=error_logs,
                context=context,
                sid=sid,
            )

            if not fix_result.get('success'):
                self.emit_log(
                    f"❌ Healer could not fix: {fix_result.get('error', 'unknown')}",
                    "error", sid
                )
                break

            self.emit_log(
                f"✅ Healer fixed: {fix_result.get('fix_description', 'N/A')[:120]}",
                "success", sid
            )
            self.emit_log(f"   Files changed: {len(fix_result.get('files_changed', []))}", "info", sid)
            self.emit_log("   ⏳ Waiting before retry...", "info", sid)
            time.sleep(5)

        # All attempts failed
        self.failed_recoveries += 1
        self.recovery_history.append({
            'action': action_name,
            'attempts': max_attempts,
            'success': False,
            'last_error': last_error,
            'timestamp': datetime.now().isoformat(),
        })

        return {
            'success': False,
            'error': f'{action_name} failed after {max_attempts} attempts: {last_error}',
            'attempts': max_attempts,
            'last_error': last_error,
            'total_elapsed': time.time() - start_time,
        }

    # ============================================
    # Delegate to HealerAgent
    # ============================================
    def _delegate_to_healer(
        self,
        action_name: str,
        error: str,
        repo_url: str,
        error_logs: str,
        context: Dict,
        sid: Optional[str] = None,
    ) -> Dict:
        """Send error to HealerAgent for fixing."""
        try:
            # Lazy import to avoid circular dependency
            from .healer_agent import HealerAgent

            healer = HealerAgent()

            heal_payload = {
                'action': 'fix',
                'repo_url': repo_url,
                'error_message': f'[{action_name}] {error[:1500]}',
                'error_logs': error_logs[:5000] if error_logs else '',
                'max_attempts': 2,
                'context': {
                    'action': action_name,
                    **(context or {}),
                },
            }

            result = healer.process(heal_payload, {**(context or {}), 'sid': sid})
            return result

        except Exception as e:
            self.emit_log(f"❌ Healer exception: {str(e)[:150]}", "error", sid)
            return {'success': False, 'error': str(e)}

    # ============================================
    # Metrics
    # ============================================
    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {
            **base,
            'total_recoveries': self.total_recoveries,
            'successful_recoveries': self.successful_recoveries,
            'failed_recoveries': self.failed_recoveries,
            'recovery_rate': (
                (self.successful_recoveries / self.total_recoveries * 100)
                if self.total_recoveries > 0 else 0
            ),
        }

    def get_recovery_history(self, limit: int = 20) -> List[Dict]:
        """Get recent recovery history."""
        return self.recovery_history[-limit:]