"""
Vercel Deploy Provider
Best for: Frontend (React, Next.js, Vue, Static)
"""

import os
import re
import time
import shutil
import subprocess
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import requests


class VercelProvider:
    """Deploys repos to Vercel."""

    name = 'vercel'
    display_name = 'Vercel'
    supports = ['node', 'static']

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_path = os.path.join(backend_dir, '.env')
        load_dotenv(env_path, override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.vercel_token = os.getenv('VERCEL_TOKEN')

    def can_deploy(self, stack: Dict[str, Any]) -> bool:
        """Check if this provider can handle the stack."""
        return stack.get('type') in ['node', 'static']

    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url')
        project_name = payload.get('project_name') or 'my-app'
        repo_id = payload.get('repo_id')
        default_branch = payload.get('default_branch', 'main')
        root_dir = payload.get('root_dir')

        owner, repo = self._parse_url(repo_url)

        def log(msg, level='info'):
            print(f"[VERCEL] {msg}")
            if on_log:
                on_log(msg, level)

        project_name = self._sanitize_name(project_name)

        # STEP 1: Create project
        log(f'Creating Vercel project "{project_name}"...', 'info')
        project = self._create_project(project_name, root_dir)

        if not project.get('success'):
            return {'success': False, 'error': project.get('error')}

        log(f'Project created: {project.get("name")}', 'success')

        # STEP 2: Trigger deploy
        log('Triggering deployment...', 'info')
        deploy = self._trigger_deploy(
            project.get('id'), owner, repo, default_branch, repo_id
        )

        if not deploy.get('success'):
            return {'success': False, 'error': deploy.get('error')}

        deploy_id = deploy.get('id')
        log(f'Deploy triggered: {deploy_id}', 'success')

        # STEP 3: Poll status
        log('Waiting for deployment...', 'info')
        live_url, error_msg = self._wait_for_deploy(deploy_id, project.get('name'), on_log=log)

        if live_url:
            return {
                'success': True,
                'status': 'deployed',
                'live_url': live_url,
                'deploy_id': deploy_id,
                'project_name': project.get('name'),
                'provider': self.name,
            }
        else:
            return {
                'success': False,
                'status': 'failed',
                'error': error_msg or 'Build failed',
                'deploy_id': deploy_id,
                'project_name': project.get('name'),
            }

    # ============================================
    # Helpers
    # ============================================
    def _parse_url(self, url: str) -> tuple:
        m = re.match(r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$', url.strip())
        if m:
            return m.group(1), m.group(2)
        return None, None

    def _sanitize_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r'[^a-z0-9._\-]', '-', name)
        name = re.sub(r'-{2,}', '-', name)
        name = name.strip('-.')
        return (name[:100] or 'devops-app')

    def _create_project(self, name: str, root_dir: Optional[str]) -> Dict[str, Any]:
        try:
            body = {'name': name, 'framework': None}
            if root_dir:
                body['rootDirectory'] = root_dir

            resp = requests.post(
                'https://api.vercel.com/v10/projects',
                headers={
                    'Authorization': f'Bearer {self.vercel_token}',
                    'Content-Type': 'application/json',
                },
                json=body,
                timeout=20,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id'), 'name': data.get('name')}

            if resp.status_code == 409:
                get_resp = requests.get(
                    f'https://api.vercel.com/v9/projects/{name}',
                    headers={'Authorization': f'Bearer {self.vercel_token}'},
                    timeout=15,
                )
                if get_resp.status_code == 200:
                    data = get_resp.json()
                    return {'success': True, 'id': data.get('id'), 'name': data.get('name')}

            return {'success': False, 'error': f'Vercel API {resp.status_code}: {resp.text[:300]}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _trigger_deploy(self, project_id, owner, repo, branch, repo_id) -> Dict[str, Any]:
        try:
            body = {
                'name': repo,
                'project': project_id,
                'gitSource': {
                    'type': 'github',
                    'ref': branch,
                    'repoId': repo_id,
                },
                'target': 'production',
            }

            resp = requests.post(
                'https://api.vercel.com/v13/deployments',
                headers={
                    'Authorization': f'Bearer {self.vercel_token}',
                    'Content-Type': 'application/json',
                },
                json=body,
                timeout=20,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id')}

            return {'success': False, 'error': f'Vercel deploy {resp.status_code}: {resp.text[:300]}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _wait_for_deploy(self, deploy_id, project_name, timeout=300, on_log=None):
        """Poll status. Returns (live_url, error_message)."""
        start = time.time()
        last_state = None

        while time.time() - start < timeout:
            try:
                resp = requests.get(
                    f'https://api.vercel.com/v13/deployments/{deploy_id}',
                    headers={'Authorization': f'Bearer {self.vercel_token}'},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    state = data.get('readyState') or data.get('status')

                    if state != last_state:
                        last_state = state
                        elapsed = int(time.time() - start)
                        if on_log:
                            on_log(f'[{elapsed}s] Status: {state}', 'info')

                    if state in ('READY', 'ready'):
                        url = data.get('url') or f'{project_name}.vercel.app'
                        return (f'https://{url}', None)
                    elif state in ('ERROR', 'error', 'CANCELED'):
                        error = data.get('error', {})
                        msg = error.get('message', 'Build failed') if isinstance(error, dict) else str(error)
                        return (None, msg)

            except Exception as e:
                print(f"Poll error: {e}")

            time.sleep(5)

        return (None, 'Deployment timeout')