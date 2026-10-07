"""
MonitorService — Real-time HTTP monitoring
===========================================
Background thread polls URLs every 30s.
Stores uptime, latency, status.
Syncs with action_store.
"""

import os
import time
import json
import threading
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class MonitorService:
    """Background HTTP monitoring service."""

    _lock = threading.Lock()
    _instance = None

    def __init__(self, root: Optional[str] = None):
        self.root = root or os.getenv(
            'SELF_HOST_ROOT', 'D:/dev/final_project/deployments'
        )
        os.makedirs(self.root, exist_ok=True)
        self.file = os.path.join(self.root, '_monitors.json')

        self.monitors = {}          # monitor_id → {url, action_id, ...}
        self.threads = {}           # monitor_id → thread
        self.stop_flags = {}        # monitor_id → Event
        self._load()

    # ============================================
    # SINGLETON
    # ============================================
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MonitorService()
        return cls._instance

    # ============================================
    # PERSISTENCE
    # ============================================
    def _load(self):
        with self._lock:
            if os.path.exists(self.file):
                try:
                    with open(self.file) as f:
                        self.monitors = json.load(f).get('monitors', {})
                except Exception:
                    self.monitors = {}

    def _save(self):
        with self._lock:
            try:
                with open(self.file, 'w') as f:
                    json.dump({'monitors': self.monitors}, f, indent=2)
            except Exception as e:
                print(f"[MONITOR] Save error: {e}")

    # ============================================
    # START MONITOR
    # ============================================
    def start_monitor(
        self,
        url: str,
        action_id: Optional[str] = None,
        interval: int = 30,
        repo_url: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Dict:
        """Start monitoring a URL in background."""
        monitor_id = f"mnt-{int(time.time())}-{len(self.monitors)}"

        monitor = {
            'id': monitor_id,
            'url': url,
            'repo_url': repo_url,
            'project_name': project_name,
            'action_id': action_id,
            'interval': interval,
            'status': 'running',
            'checks': [],           # last N checks
            'uptime_percent': 100.0,
            'avg_latency_ms': 0,
            'total_checks': 0,
            'success_count': 0,
            'error_count': 0,
            'started_at': time.time(),
            'last_check_at': None,
            'created_at': datetime.now().isoformat(),
        }

        self.monitors[monitor_id] = monitor
        self._save()

        # Start background thread
        stop_event = threading.Event()
        self.stop_flags[monitor_id] = stop_event

        thread = threading.Thread(
            target=self._poll_loop,
            args=(monitor_id, stop_event),
            daemon=True,
        )
        thread.start()
        self.threads[monitor_id] = thread

        return monitor

    # ============================================
    # POLL LOOP
    # ============================================
    def _poll_loop(self, monitor_id: str, stop_event: threading.Event):
        """Background polling thread."""
        print(f"[MONITOR] Started {monitor_id}")

        while not stop_event.is_set():
            try:
                self._do_check(monitor_id)
            except Exception as e:
                print(f"[MONITOR] Check error for {monitor_id}: {e}")

            # Wait interval
            interval = self.monitors.get(monitor_id, {}).get('interval', 30)
            stop_event.wait(interval)

        print(f"[MONITOR] Stopped {monitor_id}")

    def _do_check(self, monitor_id: str):
        """Single HTTP check."""
        monitor = self.monitors.get(monitor_id)
        if not monitor:
            return

        url = monitor['url']
        start = time.time()

        try:
            r = requests.get(url, timeout=10, allow_redirects=True)
            latency_ms = int((time.time() - start) * 1000)
            status_code = r.status_code
            success = 200 <= status_code < 400
            error_msg = None
        except requests.exceptions.Timeout:
            latency_ms = int((time.time() - start) * 1000)
            status_code = 0
            success = False
            error_msg = 'Timeout'
        except requests.exceptions.ConnectionError:
            latency_ms = int((time.time() - start) * 1000)
            status_code = 0
            success = False
            error_msg = 'Connection failed'
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            status_code = 0
            success = False
            error_msg = str(e)[:100]

        # Update monitor
        with self._lock:
            check = {
                'timestamp': time.time(),
                'time_str': datetime.now().isoformat(),
                'status_code': status_code,
                'latency_ms': latency_ms,
                'success': success,
                'error': error_msg,
            }

            monitor['checks'].append(check)
            if len(monitor['checks']) > 100:
                monitor['checks'] = monitor['checks'][-100:]

            monitor['total_checks'] += 1
            if success:
                monitor['success_count'] += 1
            else:
                monitor['error_count'] += 1

            monitor['uptime_percent'] = round(
                (monitor['success_count'] / monitor['total_checks']) * 100, 2
            )

            # Avg latency (last 20)
            recent = [c['latency_ms'] for c in monitor['checks'][-20:] if c['success']]
            if recent:
                monitor['avg_latency_ms'] = int(sum(recent) / len(recent))

            monitor['last_check_at'] = time.time()

            # Update action_store if linked
            if monitor.get('action_id'):
                try:
                    from .action_store import action_store
                    action_store.update_action(
                        monitor['action_id'],
                        result={
                            'uptime_percent': monitor['uptime_percent'],
                            'avg_latency_ms': monitor['avg_latency_ms'],
                            'total_checks': monitor['total_checks'],
                            'last_status': status_code,
                            'last_latency_ms': latency_ms,
                            'healthy': success,
                        },
                    )
                except Exception:
                    pass

        self._save()

    # ============================================
    # QUERY
    # ============================================
    def get_monitor(self, monitor_id: str) -> Optional[Dict]:
        return self.monitors.get(monitor_id)

    def list_monitors(self) -> List[Dict]:
        return list(self.monitors.values())

    def stop_monitor(self, monitor_id: str) -> bool:
        """Stop monitoring thread."""
        if monitor_id not in self.monitors:
            return False

        # Signal stop
        flag = self.stop_flags.get(monitor_id)
        if flag:
            flag.set()

        self.monitors[monitor_id]['status'] = 'stopped'
        self.monitors[monitor_id]['stopped_at'] = time.time()
        self._save()

        return True

    def delete_monitor(self, monitor_id: str) -> bool:
        """Stop + remove."""
        if monitor_id not in self.monitors:
            return False

        self.stop_monitor(monitor_id)
        del self.monitors[monitor_id]
        self.stop_flags.pop(monitor_id, None)
        self.threads.pop(monitor_id, None)
        self._save()
        return True

    def get_stats(self) -> Dict:
        """Aggregated stats for monitoring dashboard."""
        active = [m for m in self.monitors.values() if m.get('status') == 'running']
        total = len(self.monitors)

        if not total:
            return {
                'total_monitors': 0,
                'active_monitors': 0,
                'avg_uptime': 0,
                'avg_latency': 0,
                'total_checks': 0,
                'total_errors': 0,
                'monitors': [],
            }

        total_checks = sum(m.get('total_checks', 0) for m in self.monitors.values())
        total_errors = sum(m.get('error_count', 0) for m in self.monitors.values())

        avg_uptime = round(
            sum(m.get('uptime_percent', 100) for m in self.monitors.values()) / total, 2
        )
        avg_latency = int(
            sum(m.get('avg_latency_ms', 0) for m in self.monitors.values()) / total
        )

        return {
            'total_monitors': total,
            'active_monitors': len(active),
            'avg_uptime': avg_uptime,
            'avg_latency': avg_latency,
            'total_checks': total_checks,
            'total_errors': total_errors,
            'monitors': list(self.monitors.values()),
        }


# Global instance
monitor_service = MonitorService.get_instance()