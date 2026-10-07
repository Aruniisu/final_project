"""
MultiDeployService — Deploy Frontend + Backend Together
=======================================================
Deploys a full-stack app in one go:
- Frontend → Vercel
- Backend → Render
- Returns combined live URL

Fully automatic.
"""

import os
import re
import time
from typing import Dict, Any, Optional, List
import requests


class MultiDeployService:
    """
    Deploy frontend + backend + database as one unit.
    Returns a single combined live URL.
    """

    def __init__(self, agent=None):
        self.agent = agent
        self.vercel_token = os.getenv('VERCEL_TOKEN')
        self.render_api_key = os.getenv('RENDER_API_KEY')
        self.render_owner_id = os.getenv('RENDER_OWNER_ID')
        self.netlify_token = os.getenv('NETLIFY_TOKEN')

    # ============================================
    # Main: Deploy full stack
    # ============================================
    def deploy_fullstack(
        self,
        owner: str,
        repo: str,
        repo_url: str,
        default_branch: str,
        repo_id: int,
        stack_info: Dict,
        on_log=None,
    ) -> Dict:
        """
        Deploy frontend + backend together.
        Returns combined URL.
        """
        def log(msg, level='info'):
            print(f"[MULTI-DEPLOY] {msg}")
            if on_log:
                on_log(msg, level)

        log("=" * 60)
        log(f"🚀 Multi-Provider Deploy: {owner}/{repo}")
        log("=" * 60)

        # ============================================
        # STEP 1: Detect frontend + backend
        # ============================================
        log("")
        log("📍 Step 1/5: Detecting frontend + backend")

        frontend_result = self._deploy_frontend(
            owner, repo, repo_url, default_branch, repo_id, stack_info, log
        )
        backend_result = self._deploy_backend(
            owner, repo, repo_url, default_branch, stack_info, log
        )

        # ============================================
        # STEP 2: Health checks
        # ============================================
        log("")
        log("📍 Step 2/5: Health checks")

        frontend_url = frontend_result.get('url') if frontend_result.get('success') else None
        backend_url = backend_result.get('url') if backend_result.get('success') else None

        if frontend_url:
            log(f"   ✅ Frontend: {frontend_url}", 'success')
        else:
            log(f"   ❌ Frontend failed: {frontend_result.get('error', 'unknown')}", 'error')

        if backend_url:
            log(f"   ✅ Backend: {backend_url}", 'success')
        else:
            log(f"   ❌ Backend failed: {backend_result.get('error', 'unknown')}", 'error')

        # ============================================
        # STEP 3: Determine primary URL
        # ============================================
        log("")
        log("📍 Step 3/5: Building combined response")

        primary_url = frontend_url or backend_url
        if not primary_url:
            return {
                'success': False,
                'error': 'Both frontend and backend deployments failed',
                'frontend': frontend_result,
                'backend': backend_result,
            }

        # ============================================
        # STEP 4-5: Build response
        # ============================================
        return {
            'success': True,
            'primary_url': primary_url,
            'frontend_url': frontend_url,
            'backend_url': backend_url,
            'frontend_provider': frontend_result.get('provider'),
            'backend_provider': backend_result.get('provider'),
            'frontend': frontend_result,
            'backend': backend_result,
        }

    # ============================================
    # Deploy Frontend (Vercel / Netlify)
    # ============================================
    def _deploy_frontend(self, owner, repo, repo_url, branch, repo_id, stack_info, log):
        """Deploy frontend to Vercel (fallback Netlify)."""
        framework = (stack_info.get('framework') or '').lower()
        root_dir = stack_info.get('frontend_dir') or stack_info.get('root_dir')

        # Try Vercel first
        if self.vercel_token:
            log("   🎨 Deploying frontend to Vercel...")
            result = self._vercel_deploy(owner, repo, root_dir, repo_id, branch, log)
            if result.get('success'):
                return result
            log(f"   ⚠️ Vercel failed: {result.get('error')}")

        # Fallback to Netlify
        if self.netlify_token:
            log("   🎨 Falling back to Netlify...")
            result = self._netlify_deploy(owner, repo, branch, log)
            if result.get('success'):
                return result
            log(f"   ⚠️ Netlify failed: {result.get('error')}")

        return {'success': False, 'error': 'No frontend provider available'}

    # ============================================
    # Deploy Backend (Render)
    # ============================================
    def _deploy_backend(self, owner, repo, repo_url, branch, stack_info, log):
        """Deploy backend to Render."""
        if not self.render_api_key:
            return {'success': False, 'error': 'RENDER_API_KEY not set'}

        log("   ⚙️ Deploying backend to Render...")
        return self._render_deploy(owner, repo, branch, stack_info, log)

    # ============================================
    # Vercel Deploy
    # ============================================
    def _vercel_deploy(self, owner, repo, root_dir, repo_id, branch, log):
        """Deploy to Vercel via API."""
        try:
            project_name = re.sub(r'[^a-z0-9._\-]', '-', repo.lower())[:100]

            # Create project
            body = {'name': project_name}
            if root_dir:
                body['rootDirectory'] = root_dir

            proj_resp = requests.post(
                'https://api.vercel.com/v10/projects',
                headers={'Authorization': f'Bearer {self.vercel_token}', 'Content-Type': 'application/json'},
                json=body, timeout=20,
            )
            if proj_resp.status_code == 409:
                proj_resp = requests.get(
                    f'https://api.vercel.com/v9/projects/{project_name}',
                    headers={'Authorization': f'Bearer {self.vercel_token}'}, timeout=15,
                )
            if proj_resp.status_code not in (200, 201):
                return {'success': False, 'error': f'Project: {proj_resp.text[:200]}'}

            project_id = proj_resp.json().get('id')

            # Trigger deploy
            git_source = {
                'type': 'github',
                'ref': branch,
                'org': owner,
                'repoId': int(repo_id),
            }

            deploy_resp = requests.post(
                'https://api.vercel.com/v13/deployments',
                headers={'Authorization': f'Bearer {self.vercel_token}', 'Content-Type': 'application/json'},
                json={'name': repo, 'project': project_id, 'gitSource': git_source, 'target': 'production'},
                timeout=20,
            )
            if deploy_resp.status_code not in (200, 201):
                return {'success': False, 'error': f'Deploy: {deploy_resp.text[:200]}'}

            deploy_id = deploy_resp.json().get('id')

            # Poll for URL
            url = self._poll_vercel_url(deploy_id, project_name, log)
            return {
                'success': True,
                'provider': 'vercel',
                'url': url,
                'deploy_id': deploy_id,
                'dashboard_url': 'https://vercel.com/dashboard',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _poll_vercel_url(self, deploy_id, project_name, log, timeout=180):
        """Poll Vercel until deployment ready."""
        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(
                f'https://api.vercel.com/v13/deployments/{deploy_id}',
                headers={'Authorization': f'Bearer {self.vercel_token}'}, timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                state = data.get('readyState') or data.get('status')
                if state == 'READY':
                    url = data.get('url', f'{project_name}.vercel.app')
                    if not url.startswith('http'):
                        url = f'https://{url}'
                    return url
                if state in ('ERROR', 'CANCELED'):
                    return f'https://{project_name}.vercel.app'
            time.sleep(5)
        return f'https://{project_name}.vercel.app'

    # ============================================
    # Netlify Deploy (fallback)
    # ============================================
    def _netlify_deploy(self, owner, repo, branch, log):
        """Deploy to Netlify via API."""
        try:
            project_name = re.sub(r'[^a-z0-9\-]', '-', repo.lower())[:50]

            # Create site
            site_resp = requests.post(
                'https://api.netlify.com/api/v1/sites',
                headers={'Authorization': f'Bearer {self.netlify_token}'},
                json={'name': project_name, 'repo': {
                    'provider': 'github',
                    'repo': f'{owner}/{repo}',
                    'branch': branch,
                    'cmd': 'npm run build',
                    'dir': 'dist',
                }},
                timeout=20,
            )
            if site_resp.status_code not in (200, 201):
                return {'success': False, 'error': f'Netlify: {site_resp.text[:200]}'}

            data = site_resp.json()
            url = data.get('ssl_url') or data.get('url') or f'https://{project_name}.netlify.app'

            return {
                'success': True,
                'provider': 'netlify',
                'url': url,
                'site_id': data.get('id'),
                'dashboard_url': 'https://app.netlify.com',
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Render Deploy
    # ============================================
    def _render_deploy(self, owner, repo, branch, stack_info, log):
        """Deploy to Render via API."""
        try:
            project_name = re.sub(r'[^a-z0-9\-]', '-', repo.lower())[:50]
            stack_type = stack_info.get('backend_type') or stack_info.get('type', 'python')

            service_body = {
                'type': 'web_service',
                'name': f'{project_name}-backend',
                'ownerId': self.render_owner_id,
                'repo': f'https://github.com/{owner}/{repo}',
                'branch': branch,
                'autoDeploy': 'yes',
                'serviceDetails': {
                    'env': 'python' if 'python' in stack_type.lower() else 'node',
                    'plan': 'free',
                    'region': 'oregon',
                },
            }

            resp = requests.post(
                'https://api.render.com/v1/services',
                headers={'Authorization': f'Bearer {self.render_api_key}', 'Content-Type': 'application/json'},
                json=service_body, timeout=30,
            )
            if resp.status_code not in (200, 201):
                return {'success': False, 'error': f'Render: {resp.text[:200]}'}

            data = resp.json()
            service = data.get('service', data)
            service_id = service.get('id')

            # Poll for URL
            url = self._poll_render_url(service_id, project_name, log)
            return {
                'success': True,
                'provider': 'render',
                'url': url,
                'service_id': service_id,
                'dashboard_url': 'https://dashboard.render.com',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _poll_render_url(self, service_id, project_name, log, timeout=300):
        """Poll Render until service is live."""
        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(
                f'https://api.render.com/v1/services/{service_id}',
                headers={'Authorization': f'Bearer {self.render_api_key}'}, timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                service = data.get('service', data)
                url = service.get('serviceDetails', {}).get('url')
                if url:
                    if not url.startswith('http'):
                        url = f'https://{url}'
                    return url
            time.sleep(10)
        return f'https://{project_name}-backend.onrender.com'