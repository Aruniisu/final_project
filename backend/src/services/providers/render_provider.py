"""
Render Deploy Provider
Best for: Python/Node.js backends, Full-stack apps
API Docs: https://api-docs.render.com/
"""

import os
import re
import time
from typing import Dict, Any, Optional

import requests


class RenderProvider:
    """Deploys repos to Render.com."""

    name = 'render'
    display_name = 'Render'
    supports = ['python', 'node', 'docker']

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_path = os.path.join(backend_dir, '.env')
        load_dotenv(env_path, override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.render_api_key = os.getenv('RENDER_API_KEY')
        self.render_owner_id = os.getenv('RENDER_OWNER_ID')  # Optional

    def can_deploy(self, stack: Dict[str, Any]) -> bool:
        return stack.get('type') in ['python', 'node', 'docker']

    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url')
        project_name = payload.get('project_name') or 'my-app'
        default_branch = payload.get('default_branch', 'main')
        root_dir = payload.get('root_dir')
        stack = payload.get('stack', {})

        owner, repo = self._parse_url(repo_url)

        def log(msg, level='info'):
            print(f"[RENDER] {msg}")
            if on_log:
                on_log(msg, level)

        if not self.render_api_key:
            return {'success': False, 'error': 'RENDER_API_KEY not set in .env'}

        project_name = self._sanitize_name(project_name)

        # STEP 1: Create service
        log(f'Creating Render service "{project_name}"...', 'info')

        service_type = 'web_service'
        env = 'python' if stack.get('type') == 'python' else 'node'
        build_command = 'pip install -r requirements.txt' if env == 'python' else 'npm install'
        start_command = 'gunicorn app:app' if env == 'python' else 'npm start'

        service = self._create_service(
            name=project_name,
            owner=owner,
            repo=repo,
            branch=default_branch,
            root_dir=root_dir,
            env=env,
            build_command=build_command,
            start_command=start_command,
        )

        if not service.get('success'):
            return {'success': False, 'error': service.get('error')}

        log(f'Service created: {service.get("name")}', 'success')
        service_id = service.get('id')

        # STEP 2: Trigger deploy
        log('Triggering deployment...', 'info')
        deploy = self._trigger_deploy(service_id)

        if not deploy.get('success'):
            return {'success': False, 'error': deploy.get('error')}

        log(f'Deploy triggered: {deploy.get("id")}', 'success')

        # STEP 3: Poll status
        log('Waiting for deployment (up to 10 minutes)...', 'info')
        live_url, error_msg = self._wait_for_deploy(
            service_id, project_name, timeout=600, on_log=log
        )

        if live_url:
            return {
                'success': True,
                'status': 'deployed',
                'live_url': live_url,
                'provider': self.name,
                'service_id': service_id,
            }
        else:
            return {
                'success': False,
                'status': 'failed',
                'error': error_msg or 'Build failed',
                'provider': self.name,
                'service_id': service_id,
            }

    def _parse_url(self, url: str) -> tuple:
        m = re.match(r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$', url.strip())
        if m:
            return m.group(1), m.group(2)
        return None, None

    def _sanitize_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r'[^a-z0-9\-]', '-', name)
        name = re.sub(r'-{2,}', '-', name)
        name = name.strip('-')
        return (name[:63] or 'devops-app')

    def _create_service(self, name, owner, repo, branch, root_dir, env, build_command, start_command) -> Dict:
        try:
            payload = {
                'type': 'web_service',
                'name': name,
                'ownerId': self.render_owner_id,  # Required by Render API
                'repo': f'https://github.com/{owner}/{repo}',
                'branch': branch,
                'autoDeploy': 'yes',
                'serviceDetails': {
                    'env': env,
                    'region': 'oregon',
                    'plan': 'free',
                    'buildCommand': build_command,
                    'startCommand': start_command,
                },
            }
            if root_dir:
                payload['serviceDetails']['rootDir'] = root_dir

            resp = requests.post(
                'https://api.render.com/v1/services',
                headers={
                    'Authorization': f'Bearer {self.render_api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                json=payload,
                timeout=30,
            )

            print(f"Render create service: {resp.status_code}")

            if resp.status_code in (200, 201):
                data = resp.json()
                service = data.get('service') or data
                return {
                    'success': True,
                    'id': service.get('id'),
                    'name': service.get('name'),
                }

            return {'success': False, 'error': f'Render API {resp.status_code}: {resp.text[:300]}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _trigger_deploy(self, service_id: str) -> Dict:
        try:
            resp = requests.post(
                f'https://api.render.com/v1/services/{service_id}/deploys',
                headers={
                    'Authorization': f'Bearer {self.render_api_key}',
                    'Content-Type': 'application/json',
                },
                json={'clearCache': 'do_not_clear'},
                timeout=20,
            )
            if resp.status_code in (200, 201, 202):
                data = resp.json()
                return {'success': True, 'id': data.get('id')}

            return {'success': False, 'error': f'Render deploy {resp.status_code}: {resp.text[:200]}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _wait_for_deploy(self, service_id: str, project_name: str, timeout: int = 600, on_log=None):
        start = time.time()
        last_status = None

        while time.time() - start < timeout:
            try:
                resp = requests.get(
                    f'https://api.render.com/v1/services/{service_id}/deploys?limit=1',
                    headers={
                        'Authorization': f'Bearer {self.render_api_key}',
                        'Accept': 'application/json',
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    deploys = resp.json()
                    if deploys and isinstance(deploys, list):
                        status = deploys[0].get('deploy', {}).get('status') or deploys[0].get('status')

                        if status != last_status:
                            last_status = status
                            elapsed = int(time.time() - start)
                            if on_log:
                                on_log(f'[{elapsed}s] Status: {status}', 'info')

                        if status == 'live':
                            url = f'https://{project_name}.onrender.com'
                            return (url, None)
                        elif status in ('build_failed', 'canceled', 'failed'):
                            return (None, f'Render build failed: {status}')

            except Exception as e:
                print(f"Render poll error: {e}")

            time.sleep(10)

        return (None, 'Render deployment timeout')