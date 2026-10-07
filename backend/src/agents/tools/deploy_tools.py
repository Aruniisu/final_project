"""
Deploy Tools — Vercel + Render Integration
===========================================
Tools for deploying applications to Vercel and Render.

Features:
- Auto stack detection
- Vercel deployment (with gitSource.org + repoId fix)
- Render deployment
- URL polling
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests


def register_deploy_tools(registry, agent):
    """Register all deploy tools."""

    # ============================================
    # Tool 1: Detect stack
    # ============================================
    @registry.register_tool(
        name='detect_stack',
        description='Detect project stack type and framework',
        parameters={
            'repo_path': {'type': 'string', 'description': 'Path to cloned repo'},
        },
    )
    def detect_stack(repo_path: str) -> Dict:
        """Detect stack from repo files."""
        try:
            root = Path(repo_path)

            # Check for package.json (Node)
            pkg_json = root / 'package.json'
            if pkg_json.exists():
                import json as _json
                with open(pkg_json, 'r', encoding='utf-8') as f:
                    pkg = _json.load(f)

                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

                # Detect framework
                framework = 'node'
                if 'next' in deps:
                    framework = 'next'
                elif 'react' in deps:
                    framework = 'react'
                elif 'vue' in deps:
                    framework = 'vue'
                elif 'svelte' in deps:
                    framework = 'svelte'
                elif 'express' in deps:
                    framework = 'express'
                elif 'vite' in deps:
                    framework = 'vite'

                # Check subdirs
                root_dir = None
                for candidate in ['frontend', 'client', 'web', 'app']:
                    if (root / candidate / 'package.json').exists():
                        root_dir = candidate
                        break

                return {
                    'success': True,
                    'type': 'node',
                    'framework': framework,
                    'root_dir': root_dir,
                }

            # Check for Python
            if (root / 'requirements.txt').exists() or (root / 'pyproject.toml').exists():
                framework = 'python'
                if (root / 'manage.py').exists():
                    framework = 'django'
                elif (root / 'app.py').exists():
                    with open(root / 'app.py', 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(500)
                        if 'FastAPI' in content:
                            framework = 'fastapi'
                        elif 'Flask' in content:
                            framework = 'flask'

                return {
                    'success': True,
                    'type': 'python',
                    'framework': framework,
                    'root_dir': None,
                }

            # Check for Docker
            if (root / 'Dockerfile').exists():
                return {
                    'success': True,
                    'type': 'docker',
                    'framework': 'docker',
                    'root_dir': None,
                }

            # Check for static HTML
            if (root / 'index.html').exists():
                return {
                    'success': True,
                    'type': 'static',
                    'framework': 'static',
                    'root_dir': None,
                }

            return {
                'success': True,
                'type': 'node',
                'framework': 'unknown',
                'root_dir': None,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 2: Vercel deploy
    # ============================================
    @registry.register_tool(
        name='vercel_deploy',
        description='Deploy application to Vercel',
        parameters={
            'owner': {'type': 'string', 'description': 'GitHub owner'},
            'repo': {'type': 'string', 'description': 'GitHub repo name'},
            'project_name': {'type': 'string', 'description': 'Vercel project name'},
            'root_dir': {'type': 'string', 'description': 'Root directory (optional)'},
            'repo_id': {'type': 'integer', 'description': 'GitHub repo ID (optional)'},
            'branch': {'type': 'string', 'description': 'Branch (default: main)'},
        },
    )
    def vercel_deploy(
        owner: str,
        repo: str,
        project_name: str,
        root_dir: Optional[str] = None,
        repo_id: Optional[int] = None,
        branch: str = 'main',
    ) -> Dict:
        """Deploy to Vercel via API."""
        token = os.getenv('VERCEL_TOKEN')
        if not token:
            return {'success': False, 'error': 'VERCEL_TOKEN not set'}

        try:
            print(f"[VERCEL-DEBUG] owner={owner}, repo={repo}, project_name={project_name}")
            print(f"[VERCEL-DEBUG] root_dir={root_dir}, repo_id={repo_id}, branch={branch}")

            # ⭐ AUTO-FETCH repo_id if missing
            if not repo_id:
                print(f"[VERCEL-DEBUG] repo_id missing — fetching from GitHub API...")
                gh_token = os.getenv('GITHUB_TOKEN')
                if gh_token:
                    try:
                        gh_resp = requests.get(
                            f'https://api.github.com/repos/{owner}/{repo}',
                            headers={
                                'Authorization': f'token {gh_token}',
                                'Accept': 'application/vnd.github+json',
                            },
                            timeout=15,
                        )
                        if gh_resp.status_code == 200:
                            repo_id = gh_resp.json().get('id')
                            print(f"[VERCEL-DEBUG] ✅ Fetched repo_id: {repo_id}")
                        else:
                            print(f"[VERCEL-DEBUG] ⚠️ GitHub API {gh_resp.status_code}")
                    except Exception as e:
                        print(f"[VERCEL-DEBUG] ⚠️ Fetch failed: {e}")

            if not repo_id:
                return {
                    'success': False,
                    'error': 'repoId is required for Vercel deployment but could not be fetched',
                }

            # Sanitize project name
            project_name = re.sub(r'[^a-z0-9._\-]', '-', project_name.lower())[:100]

            # ============================================
            # STEP 1: Create or get Vercel project
            # ============================================
            body = {'name': project_name, 'framework': None}
            if root_dir:
                body['rootDirectory'] = root_dir

            proj_resp = requests.post(
                'https://api.vercel.com/v10/projects',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json=body,
                timeout=20,
            )

            if proj_resp.status_code == 409:
                # Project exists — fetch it
                proj_resp = requests.get(
                    f'https://api.vercel.com/v9/projects/{project_name}',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=15,
                )

            if proj_resp.status_code not in (200, 201):
                return {
                    'success': False,
                    'error': f'Vercel project create failed ({proj_resp.status_code}): {proj_resp.text[:200]}',
                }

            project_data = proj_resp.json()
            project_id = project_data.get('id')

            if not project_id:
                return {
                    'success': False,
                    'error': f'Vercel project created but no ID returned: {proj_resp.text[:200]}',
                }

            # ============================================
            # STEP 2: Build gitSource with org + repoId
            # ============================================
            git_source = {
                'type': 'github',
                'ref': branch,
                'org': owner,                # ⭐ REQUIRED
                'repoId': int(repo_id),      # ⭐ REQUIRED (integer)
            }

            print(f"[VERCEL-DEBUG] git_source = {git_source}")

            deploy_body = {
                'name': repo,
                'project': project_id,
                'gitSource': git_source,
                'target': 'production',
            }

            print(f"[VERCEL-DEBUG] deploy_body = {deploy_body}")

            # ============================================
            # STEP 3: Trigger deployment
            # ============================================
            deploy_resp = requests.post(
                'https://api.vercel.com/v13/deployments',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json=deploy_body,
                timeout=20,
            )

            print(f"[VERCEL-DEBUG] deploy_resp.status = {deploy_resp.status_code}")

            if deploy_resp.status_code not in (200, 201):
                return {
                    'success': False,
                    'error': f'Vercel deploy failed ({deploy_resp.status_code}): {deploy_resp.text[:300]}',
                }

            deploy_data = deploy_resp.json()
            print(f"[VERCEL-DEBUG] ✅ Deploy created: {deploy_data.get('id')}")

            return {
                'success': True,
                'deploy_id': deploy_data.get('id'),
                'project_id': project_id,
                'project_name': project_name,
                'provider': 'vercel',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 3: Vercel get URL (poll status)
    # ============================================
    @registry.register_tool(
        name='vercel_get_url',
        description='Poll Vercel deployment status and return live URL when ready',
        parameters={
            'deploy_id': {'type': 'string', 'description': 'Vercel deploy ID'},
            'project_name': {'type': 'string', 'description': 'Project name'},
            'timeout': {'type': 'integer', 'description': 'Max wait seconds (default 180)'},
        },
    )
    def vercel_get_url(deploy_id: str, project_name: str, timeout: int = 180) -> Dict:
        """Poll Vercel deploy until ready + return URL."""
        token = os.getenv('VERCEL_TOKEN')
        if not token:
            return {'success': False, 'error': 'VERCEL_TOKEN not set'}

        try:
            start = time.time()
            last_status = None

            while time.time() - start < timeout:
                resp = requests.get(
                    f'https://api.vercel.com/v13/deployments/{deploy_id}',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=15,
                )

                if resp.status_code != 200:
                    time.sleep(5)
                    continue

                data = resp.json()
                ready_state = data.get('readyState') or data.get('status')
                last_status = ready_state

                if ready_state == 'READY':
                    url = data.get('url', f'{project_name}.vercel.app')
                    if not url.startswith('http'):
                        url = f'https://{url}'
                    return {'success': True, 'url': url, 'status': 'ready'}

                if ready_state in ('ERROR', 'CANCELED'):
                    return {
                        'success': False,
                        'error': f'Deployment {ready_state}',
                        'url': f'https://{project_name}.vercel.app',
                    }

                time.sleep(5)

            # Timeout — return fallback URL
            return {
                'success': True,
                'url': f'https://{project_name}.vercel.app',
                'status': 'timeout',
                'last_status': last_status,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 4: Render deploy
    # ============================================
    @registry.register_tool(
        name='render_deploy',
        description='Deploy application to Render',
        parameters={
            'owner': {'type': 'string', 'description': 'GitHub owner'},
            'repo': {'type': 'string', 'description': 'GitHub repo name'},
            'project_name': {'type': 'string', 'description': 'Render service name'},
            'stack_type': {'type': 'string', 'description': 'Stack (node/python/etc)'},
            'branch': {'type': 'string', 'description': 'Branch (default: main)'},
        },
    )
    def render_deploy(
        owner: str,
        repo: str,
        project_name: str,
        stack_type: str = 'node',
        branch: str = 'main',
    ) -> Dict:
        """Deploy to Render via API."""
        api_key = os.getenv('RENDER_API_KEY')
        owner_id = os.getenv('RENDER_OWNER_ID')

        if not api_key:
            return {'success': False, 'error': 'RENDER_API_KEY not set'}

        try:
            # Sanitize name
            service_name = re.sub(r'[^a-z0-9\-]', '-', project_name.lower())[:50]

            # Build service spec
            service_body = {
                'type': 'web_service',
                'name': service_name,
                'ownerId': owner_id,
                'repo': f'https://github.com/{owner}/{repo}',
                'branch': branch,
                'autoDeploy': 'yes',
                'serviceDetails': {
                    'env': 'node' if stack_type == 'node' else 'python',
                    'plan': 'free',
                    'region': 'oregon',
                },
            }

            # Node-specific config
            if stack_type == 'node':
                service_body['serviceDetails'].update({
                    'envSpecificDetails': {
                        'buildCommand': 'npm install && npm run build',
                        'startCommand': 'npm start',
                    },
                })
            elif stack_type == 'python':
                service_body['serviceDetails'].update({
                    'envSpecificDetails': {
                        'buildCommand': 'pip install -r requirements.txt',
                        'startCommand': 'gunicorn app:app',
                    },
                })

            resp = requests.post(
                'https://api.render.com/v1/services',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                json=service_body,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                return {
                    'success': False,
                    'error': f'Render deploy failed ({resp.status_code}): {resp.text[:300]}',
                }

            data = resp.json()
            service = data.get('service', data)
            service_id = service.get('id')

            return {
                'success': True,
                'service_id': service_id,
                'project_name': service_name,
                'provider': 'render',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 5: Render get URL
    # ============================================
    @registry.register_tool(
        name='render_get_url',
        description='Poll Render service status and return live URL',
        parameters={
            'service_id': {'type': 'string', 'description': 'Render service ID'},
            'project_name': {'type': 'string', 'description': 'Service name'},
            'timeout': {'type': 'integer', 'description': 'Max wait seconds (default 300)'},
        },
    )
    def render_get_url(service_id: str, project_name: str, timeout: int = 300) -> Dict:
        """Poll Render service until live + return URL."""
        api_key = os.getenv('RENDER_API_KEY')
        if not api_key:
            return {'success': False, 'error': 'RENDER_API_KEY not set'}

        try:
            start = time.time()

            while time.time() - start < timeout:
                resp = requests.get(
                    f'https://api.render.com/v1/services/{service_id}',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Accept': 'application/json',
                    },
                    timeout=15,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    service = data.get('service', data)
                    url = service.get('serviceDetails', {}).get('url')

                    if url:
                        if not url.startswith('http'):
                            url = f'https://{url}'
                        return {'success': True, 'url': url, 'status': 'live'}

                time.sleep(10)

            # Timeout — return fallback
            return {
                'success': True,
                'url': f'https://{project_name}.onrender.com',
                'status': 'timeout',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}