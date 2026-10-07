"""
Universal Auto-Fix Workflow
============================
Provides retry-with-fix capability for ANY agent action.

Use cases:
- Deploy fails → auto-fix → retry
- Pipeline fails → auto-fix → retry
- Build fails → auto-fix → retry
- Any agent action → if fails → fix → retry

Features:
- Reflection-based retry
- HealerAgent integration
- Max attempts configurable
- Real-time streaming logs
"""

import time
import traceback
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime


class AutoFixWorkflow:
    """
    Universal workflow that wraps any action with auto-fix retry logic.
    """

    def __init__(self, healer_agent=None, max_attempts: int = 3):
        """
        Args:
            healer_agent: HealerAgent instance for fixing
            max_attempts: Max retry attempts (default 3)
        """
        self.healer = healer_agent
        self.max_attempts = max_attempts
        self.history: List[Dict] = []

    # ============================================
    # Main: Execute with auto-fix
    # ============================================
    def execute_with_retry(
        self,
        action_fn: Callable,
        action_name: str,
        context: Optional[Dict] = None,
        fix_context: Optional[Dict] = None,
        on_log: Optional[Callable] = None,
    ) -> Dict:
        """
        Execute an action with automatic retry + fix.

        Args:
            action_fn: Callable() -> Dict that performs the action
            action_name: Human-readable name (e.g., "deploy", "pipeline")
            context: Action context
            fix_context: Additional context for the healer
            on_log: Logging callback(message, level)

        Returns:
            Final result dict from action_fn
        """

        def log(msg, level='info'):
            print(f"[AUTO-FIX] {msg}")
            if on_log:
                on_log(msg, level)

        context = context or {}
        fix_context = fix_context or {}
        last_error = None

        log("=" * 60, 'info')
        log(f"🔄 Auto-Fix Workflow: {action_name}", 'info')
        log(f"   Max attempts: {self.max_attempts}", 'info')
        log("=" * 60, 'info')

        for attempt in range(1, self.max_attempts + 1):
            log("", 'info')
            log(f"▶️  Attempt {attempt}/{self.max_attempts}: {action_name}", 'info')

            start_time = time.time()

            try:
                result = action_fn()
                elapsed = time.time() - start_time

                if isinstance(result, dict) and result.get('success'):
                    log(f"✅ {action_name} succeeded on attempt {attempt}", 'success')
                    self.history.append({
                        'action': action_name,
                        'attempts': attempt,
                        'success': True,
                        'elapsed': elapsed,
                        'timestamp': datetime.now().isoformat(),
                    })
                    return result

                # Action failed but no exception
                last_error = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                log(f"❌ Attempt {attempt} failed: {last_error[:200]}", 'error')

            except Exception as e:
                elapsed = time.time() - start_time
                last_error = str(e)
                log(f"❌ Attempt {attempt} exception: {last_error[:200]}", 'error')
                traceback.print_exc()

            # Check if we can retry
            if attempt >= self.max_attempts:
                log("⚠️ Max attempts reached — giving up", 'error')
                break

            # Try to heal
            if not self.healer:
                log("⚠️ No HealerAgent configured — cannot auto-fix", 'warning')
                break

            log("", 'info')
            log(f"🩺 HealerAgent analyzing (attempt {attempt})...", 'info')

            fix_result = self._heal_error(
                action_name=action_name,
                error=last_error,
                context=context,
                fix_context=fix_context,
                log=log,
            )

            if not fix_result.get('success'):
                log(f"❌ Healer could not fix: {fix_result.get('error')}", 'error')
                break

            log(f"✅ Healer fixed: {fix_result.get('fix_description', 'N/A')}", 'success')
            log(f"   Files changed: {len(fix_result.get('files_changed', []))}", 'info')
            log("⏳ Waiting before retry...", 'info')
            time.sleep(3)

        # All attempts failed
        self.history.append({
            'action': action_name,
            'attempts': self.max_attempts,
            'success': False,
            'last_error': last_error,
            'timestamp': datetime.now().isoformat(),
        })

        return {
            'success': False,
            'error': f'{action_name} failed after {self.max_attempts} attempts: {last_error}',
            'attempts': self.max_attempts,
            'last_error': last_error,
        }

    # ============================================
    # Delegate to healer
    # ============================================
    def _heal_error(
        self,
        action_name: str,
        error: str,
        context: Dict,
        fix_context: Dict,
        log: Callable,
    ) -> Dict:
        """Send error to HealerAgent for fixing."""
        try:
            repo_url = context.get('repo_url') or fix_context.get('repo_url')
            if not repo_url:
                log("⚠️ No repo_url for healing", 'warning')
                return {'success': False, 'error': 'No repo_url'}

            # Build healing payload
            heal_payload = {
                'action': 'fix',
                'repo_url': repo_url,
                'error_message': error[:1500],
                'error_logs': fix_context.get('error_logs', ''),
                'context': {
                    'action': action_name,
                    'action_context': context,
                    **fix_context,
                },
            }

            result = self.healer.process(heal_payload, context)
            return result

        except Exception as e:
            log(f"❌ Healer exception: {str(e)[:150]}", 'error')
            return {'success': False, 'error': str(e)}

    # ============================================
    # Metrics
    # ============================================
    def get_stats(self) -> Dict:
        """Get workflow statistics."""
        total = len(self.history)
        if total == 0:
            return {'total': 0, 'success_rate': 0, 'avg_attempts': 0}

        success = sum(1 for h in self.history if h.get('success'))
        attempts = [h.get('attempts', 1) for h in self.history]

        return {
            'total': total,
            'success_count': success,
            'failure_count': total - success,
            'success_rate': (success / total * 100),
            'avg_attempts': sum(attempts) / total if attempts else 0,
        }