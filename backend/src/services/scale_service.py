"""
ScaleService — Premium Replica Tracker
========================================
Track virtual replicas per service.
Simulates auto-scaling behavior.
Syncs with action_store.
"""

import os
import json
import time
import random
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime


class ScaleService:
    """Premium replica tracker."""

    _lock = threading.Lock()
    _instance = None

    def __init__(self, root: Optional[str] = None):
        self.root = root or os.getenv(
            'SELF_HOST_ROOT', 'D:/dev/final_project/deployments'
        )
        os.makedirs(self.root, exist_ok=True)
        self.file = os.path.join(self.root, '_scales.json')

        self.services = {}          # service_name → {replicas, ...}
        self.metrics_thread = None
        self.stop_metrics = threading.Event()
        self._load()
        self._start_metrics_loop()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ScaleService()
        return cls._instance

    # ============================================
    # PERSISTENCE
    # ============================================
    def _load(self):
        with self._lock:
            if os.path.exists(self.file):
                try:
                    with open(self.file) as f:
                        self.services = json.load(f).get('services', {})
                except Exception:
                    self.services = {}

    def _save(self):
        with self._lock:
            try:
                with open(self.file, 'w') as f:
                    json.dump({'services': self.services}, f, indent=2)
            except Exception as e:
                print(f"[SCALE] Save error: {e}")

    # ============================================
    # METRICS LOOP (simulates real-time)
    # ============================================
    def _start_metrics_loop(self):
        self.metrics_thread = threading.Thread(
            target=self._metrics_loop, daemon=True
        )
        self.metrics_thread.start()

    def _metrics_loop(self):
        """Update metrics every 10s for all services."""
        while not self.stop_metrics.is_set():
            try:
                for svc_name in list(self.services.keys()):
                    self._update_metrics(svc_name)
            except Exception as e:
                print(f"[SCALE] Metrics error: {e}")
            self.stop_metrics.wait(10)

    def _update_metrics(self, service_name: str):
        """Simulate realistic metrics based on replica count."""
        svc = self.services.get(service_name)
        if not svc:
            return

        replicas = svc.get('replicas', 1)

        # More replicas = less CPU per replica (load distribution)
        base_cpu = 80 / max(replicas, 1)
        base_mem = 70 / max(replicas, 1)

        svc['cpu_percent'] = max(5, min(95, int(base_cpu + random.randint(-10, 10))))
        svc['memory_percent'] = max(5, min(95, int(base_mem + random.randint(-10, 10))))
        svc['requests_per_sec'] = int((50 * replicas) + random.randint(-20, 50))
        svc['last_metrics_at'] = time.time()

        # Per-replica metrics
        svc['replica_metrics'] = []
        for i in range(replicas):
            svc['replica_metrics'].append({
                'id': f"{service_name}-{i+1}",
                'cpu': max(5, min(95, svc['cpu_percent'] + random.randint(-15, 15))),
                'memory': max(5, min(95, svc['memory_percent'] + random.randint(-15, 15))),
                'status': 'running',
            })

        self._save()

    # ============================================
    # SCALE OPERATIONS
    # ============================================
    def scale_service(
        self,
        service_name: str,
        replicas: int,
        repo_url: Optional[str] = None,
        action_id: Optional[str] = None,
    ) -> Dict:
        """Scale service to N replicas."""
        replicas = max(1, min(20, int(replicas)))     # clamp 1-20

        with self._lock:
            existing = self.services.get(service_name)
            old_replicas = existing.get('replicas', 1) if existing else 1

            service = {
                'service_name': service_name,
                'replicas': replicas,
                'old_replicas': old_replicas,
                'repo_url': repo_url or (existing.get('repo_url') if existing else None),
                'action_id': action_id,
                'status': 'running',
                'cpu_percent': existing.get('cpu_percent', 45) if existing else 45,
                'memory_percent': existing.get('memory_percent', 60) if existing else 60,
                'requests_per_sec': existing.get('requests_per_sec', 50) if existing else 50,
                'replica_metrics': [],
                'started_at': existing.get('started_at') if existing else time.time(),
                'last_scaled_at': time.time(),
                'created_at': existing.get('created_at') if existing else datetime.now().isoformat(),
            }

            self.services[service_name] = service

        # Simulate scale delay (real feels)
        time.sleep(1.5)

        # Update metrics after scale
        self._update_metrics(service_name)

        # Update action_store
        if action_id:
            try:
                from .action_store import action_store
                action_store.update_action(
                    action_id,
                    status='success',
                    progress=100,
                    result={
                        'service': service_name,
                        'old_replicas': old_replicas,
                        'new_replicas': replicas,
                        'scaled_at': time.time(),
                    },
                )
            except Exception as e:
                print(f"[SCALE] action_store update error: {e}")

        return self.services.get(service_name)

    def get_service(self, service_name: str) -> Optional[Dict]:
        return self.services.get(service_name)

    def list_services(self) -> List[Dict]:
        return list(self.services.values())

    def delete_service(self, service_name: str) -> bool:
        with self._lock:
            if service_name in self.services:
                del self.services[service_name]
                self._save()
                return True
        return False

    def get_stats(self) -> Dict:
        """Aggregated stats for infrastructure page."""
        total = len(self.services)
        if not total:
            return {
                'total_services': 0,
                'total_replicas': 0,
                'avg_cpu': 0,
                'avg_memory': 0,
                'services': [],
            }

        total_replicas = sum(s.get('replicas', 0) for s in self.services.values())
        avg_cpu = int(sum(s.get('cpu_percent', 0) for s in self.services.values()) / total)
        avg_memory = int(sum(s.get('memory_percent', 0) for s in self.services.values()) / total)

        return {
            'total_services': total,
            'total_replicas': total_replicas,
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'services': list(self.services.values()),
        }


# Global instance
scale_service = ScaleService.get_instance()