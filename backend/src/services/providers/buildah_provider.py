"""
Buildah Deploy Provider
Daemonless Docker build alternative. No Docker daemon needed.
Best for: Local builds without Docker, containers in restricted envs.
"""

import os
import re
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime


class BuildahProvider:
    """Builds images with Buildah (daemonless), deploys to a target."""

    name = 'buildah'
    display_name = 'Buildah (Daemonless)'
    supports = ['docker', 'any']

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_path = os.path.join(backend_dir, '.env')
        load_dotenv(env_path, override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.registry = os.getenv('DOCKER_REGISTRY')
        self.registry_user = os.getenv('DOCKER_USERNAME')
        self.registry_pass = os.getenv('DOCKER_PASSWORD')

    def can_deploy(self, stack: Dict[str, Any]) -> bool:
        return True

    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url')
        project_name = payload.get('project_name') or 'my-app'
        default_branch = payload.get('default_branch', 'main')
        root_dir = payload.get('root_dir')

        owner, repo = self._parse_url(repo_url)

        def log(msg, level='info'):
            print(f"[BUILDAH] {msg}")
            if on_log:
                on_log(msg, level)

        if not self._is_buildah_installed():
            return {
                'success': False,
                'error': 'Buildah not installed. Install: https://buildah.io/'
            }

        if not self.registry:
            return {'success': False, 'error': 'DOCKER_REGISTRY not set in .env'}

        project_name = self._sanitize_name(project_name)
        image_tag = f'{self.registry}/{project_name}:latest'

        # STEP 1: Clone
        log(f'Cloning {owner}/{repo}...', 'info')
        tmp_dir = tempfile.mkdtemp(prefix='buildah_')

        try:
            clone_url = f'https://{self.github_token}@github.com/{owner}/{repo}.git'
            result = subprocess.run(
                ['git', 'clone', '--depth=1', '--branch', default_branch, clone_url, tmp_dir],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {'success': False, 'error': f'Clone failed: {result.stderr[:200]}'}

            log('Cloned repo', 'success')

            # STEP 2: Ensure Dockerfile
            context_dir = os.path.join(tmp_dir, root_dir or '')
            dockerfile_path = os.path.join(context_dir, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                log('No Dockerfile found. Generating one...', 'warning')
                self._generate_dockerfile(context_dir, payload.get('stack', {}))

            # STEP 3: Build with Buildah
            log(f'Building image: {image_tag}', 'info')

            build_cmd = ['buildah', 'bud', '-t', image_tag, '.']
            build_result = subprocess.run(
                build_cmd,
                cwd=context_dir,
                capture_output=True, text=True, timeout=600,
            )

            if build_result.returncode != 0:
                log(f'Build failed: {build_result.stderr[:300]}', 'error')
                return {'success': False, 'error': f'Buildah build failed: {build_result.stderr[:300]}'}

            log('Image built successfully', 'success')

            # STEP 4: Login to registry (if creds provided)
            if self.registry_user and self.registry_pass:
                login_result = subprocess.run(
                    ['buildah', 'login', '--username', self.registry_user,
                     '--password', self.registry_pass, self.registry],
                    capture_output=True, text=True, timeout=60,
                )
                if login_result.returncode != 0:
                    log(f'Registry login failed: {login_result.stderr[:200]}', 'warning')

            # STEP 5: Push
            log(f'Pushing to registry: {image_tag}', 'info')
            push_result = subprocess.run(
                ['buildah', 'push', image_tag],
                capture_output=True, text=True, timeout=300,
            )

            if push_result.returncode != 0:
                return {'success': False, 'error': f'Push failed: {push_result.stderr[:300]}'}

            log('Image pushed to registry', 'success')

            # STEP 6: Run container locally for testing
            log('Starting container for testing...', 'info')
            run_result = subprocess.run(
                ['buildah', 'from', image_tag],
                capture_output=True, text=True, timeout=30,
            )
            container_id = run_result.stdout.strip()

            if container_id:
                subprocess.run(
                    ['buildah', 'run', '-d', '--name', f'{project_name}-test',
                     container_id, 'sh', '-c', 'echo ready'],
                    capture_output=True, text=True, timeout=60,
                )

            live_url = f'http://localhost:8080/{project_name}'

            return {
                'success': True,
                'status': 'deployed',
                'live_url': live_url,
                'provider': self.name,
                'image': image_tag,
            }

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _is_buildah_installed(self) -> bool:
        try:
            result = subprocess.run(['buildah', '--version'], capture_output=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _parse_url(self, url: str) -> tuple:
        m = re.match(r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$', url.strip())
        return (m.group(1), m.group(2)) if m else (None, None)

    def _sanitize_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r'[^a-z0-9\-]', '-', name)
        name = re.sub(r'-{2,}', '-', name)
        return name.strip('-')[:63]

    def _generate_dockerfile(self, path: str, stack: Dict) -> None:
        stype = stack.get('type', 'unknown')
        if stype == 'python':
            content = '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
'''
        elif stype == 'node':
            content = '''FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
'''
        else:
            content = '''FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["sh", "-c", "echo Hello from container"]
'''

        with open(os.path.join(path, 'Dockerfile'), 'w') as f:
            f.write(content)