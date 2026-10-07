"""
ActionStore — Unified Registry for ALL Agent Actions
=====================================================
Every action (deploy/pipeline/monitor/scale/security/fix_code) is stored here.
Other pages read from this store → auto-sync.
"""

import os
import json
import time
import uuid
import threading
from typing import Dict, Any, Optional, List


class ActionStore:
    """Thread-safe unified action registry."""

    _lock = threading.Lock()

    def __init__(self, root: Optional[str] = None):
        self.root = root or os.getenv(
            'SELF_HOST_ROOT', 'D:/dev/final_project/deployments'
        )
        os.makedirs(self.root, exist_ok=True)
        self.file = os.path.join(self.root, '_actions.json')

    # ============================================
    # INTERNAL
    # ============================================
    def _read(self) -> Dict:
        with self._lock:
            if not os.path.exists(self.file):
                return {'actions': {}}
            try:
                with open(self.file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return {'actions': {}}
                    data = json.loads(content)
                    if not isinstance(data, dict):
                        return {'actions': {}}
                    data.setdefault('actions', {})
                    return data
            except Exception:
                return {'actions': {}}

    def _write(self, data: Dict):
        with self._lock:
            try:
                with open(self.file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"[ACTION-STORE] Write error: {e}")

    # ============================================
    # PUBLIC API
    # ============================================
    def start_action(
        self,
        action_type: str,
        repo_url: str = None,
        provider: str = 'self-host',
        user_id: str = 'anonymous',
        project_id: str = 'default',
        project_name: str = 'Unknown',
        extra: Dict = None,
    ) -> str:
        """Create new action → return action_id."""
        action_id = f"{action_type}-{uuid.uuid4().hex[:8]}"
        data = self._read()
        data['actions'][action_id] = {
            'id': action_id,
            'type': action_type,
            'status': 'running',
            'progress': 0,
            'repo_url': repo_url,
            'provider': provider,
            'url': None,
            'result': None,
            'error': None,
            'user_id': user_id,
            'project_id': project_id,
            'project_name': project_name,
            'extra': extra or {},
            'started_at': time.time(),
            'completed_at': None,
        }
        self._write(data)
        return action_id

    def update_action(
        self,
        action_id: str,
        status: str = None,
        progress: int = None,
        url: str = None,
        result: Dict = None,
        error: str = None,
    ):
        """Update action state."""
        data = self._read()
        action = data['actions'].get(action_id)
        if not action:
            return

        if status:
            action['status'] = status
        if progress is not None:
            action['progress'] = progress
        if url:
            action['url'] = url
        if result is not None:
            action['result'] = result
        if error:
            action['error'] = error

        if status in ('success', 'failed'):
            action['completed_at'] = time.time()

        self._write(data)

    def get_action(self, action_id: str) -> Optional[Dict]:
        return self._read()['actions'].get(action_id)

    def list_actions(
        self,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List actions, newest first."""
        data = self._read()
        actions = list(data['actions'].values())

        if action_type:
            actions = [a for a in actions if a.get('type') == action_type]
        if status:
            actions = [a for a in actions if a.get('status') == status]

        actions.sort(key=lambda a: a.get('started_at', 0), reverse=True)
        return actions[:limit]

    def delete_action(self, action_id: str) -> bool:
        data = self._read()
        if action_id in data['actions']:
            del data['actions'][action_id]
            self._write(data)
            return True
        return False

    def cleanup_old(self, max_age_seconds: int = 7200):
        """Delete actions older than N seconds."""
        data = self._read()
        now = time.time()
        removed = []
        for aid, action in list(data['actions'].items()):
            age = now - action.get('started_at', now)
            if age > max_age_seconds:
                del data['actions'][aid]
                removed.append(aid)
        if removed:
            self._write(data)
        return removed


# Global instance
action_store = ActionStore()