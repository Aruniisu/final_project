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


class RealDeployService:
    """Handles real GitHub to Vercel deployments."""

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(backend_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.vercel_token = os.getenv('VERCEL_TOKEN')

        print(f"RealDeployService initialized")
        print(f"   GITHUB_TOKEN: {'SET' if self.github_token else 'NOT SET'}")
        print(f"   VERCEL_TOKEN: {'SET' if self.vercel_token else 'NOT SET'}")

    # ============================================
    # Main entry point
    # ============================================
    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url') or payload.get('repoUrl')
        project_name = payload.get('project_name') or payload.get('projectName') or 'my-app'
        deploy_type = payload.get('deploy_type') or payload.get('deployType') or 'fullstack'

        if not repo_url:
            return {'success': False, 'error': 'No repo_url provided'}

        if not self.github_token:
            return {'success': False, 'error': 'GITHUB_TOKEN not set in .env'}

        if not self.vercel_token:
            return {'success': False, 'error': 'VERCEL_TOKEN not set in .env'}

        def log(msg, level='info'):
            print(f"[DEPLOY] {msg}")
            if on_log:
                on_log(msg, level)

        # STEP 1: Parse GitHub URL
        log(f'Parsing GitHub URL: {repo_url}', 'info')
        parsed = self._parse_github_url(repo_url)
        if not parsed:
            return {'success': False, 'error': f'Invalid GitHub URL: {repo_url}'}

        owner, repo = parsed
        log(f'Repo: {owner}/{repo}', 'success')

        # Sanitize project name for Vercel
        project_name = self._sanitize_vercel_name(project_name or repo)
        log(f'Vercel project name: {project_name}', 'info')

        # STEP 2: Check repo exists
        log('Checking if repo exists on GitHub...', 'info')
        repo_info = self._get_repo_info(owner, repo)
        if not repo_info:
            return {'success': False, 'error': f'Repo {owner}/{repo} not found or not accessible'}

        repo_id = repo_info.get('id')
        log(f'Repo found: {repo_info.get("description") or "no description"}', 'success')
        log(f'GitHub repo ID: {repo_id}', 'info')
        default_branch = repo_info.get('default_branch', 'main')
        log(f'Default branch: {default_branch}', 'info')

        # STEP 3: Clone repo
        tmp_dir = tempfile.mkdtemp(prefix='deploy_')
        try:
            log(f'Cloning {owner}/{repo}@{default_branch}...', 'info')
            clone_url = f'https://{self.github_token}@github.com/{owner}/{repo}.git'

            result = subprocess.run(
                ['git', 'clone', '--depth=1', '--branch', default_branch, clone_url, tmp_dir],
                capture_output=True, text=True, timeout=120,
            )

            if result.returncode != 0:
                err = result.stderr.replace(self.github_token, '***') if self.github_token else result.stderr
                log(f'Clone failed: {err[:200]}', 'error')
                return {'success': False, 'error': f'Clone failed: {err[:300]}'}

            log('Cloned to temp dir', 'success')

            # STEP 4: Detect stack (monorepo support)
            stack = self._detect_stack(tmp_dir)
            log(f'Detected stack: {stack["type"]} ({stack["framework"]})', 'info')

            root_dir = stack.get('root_dir') or None
            if root_dir:
                log(f'Using subfolder for deployment: {root_dir}', 'info')

            # STEP 5: Create Vercel project (rootDirectory is set HERE)
            log(f'Creating Vercel project "{project_name}"...', 'info')
            project = self._create_vercel_project(project_name, owner, repo, root_dir)

            if not project.get('success'):
                err = project.get("error", "Unknown error")
                log(f'Vercel project creation failed: {err}', 'error')
                return {'success': False, 'error': err}

            log(f'Vercel project created: {project.get("name")}', 'success')

            # STEP 6: Trigger deployment (NO rootDirectory here)
            log('Triggering deployment on Vercel...', 'info')
            deploy = self._trigger_vercel_deploy(
                project.get('id'), owner, repo, default_branch, repo_id
            )

            if not deploy.get('success'):
                err = deploy.get("error", "Deploy trigger failed")
                log(f'Deploy trigger failed: {err}', 'error')
                return {'success': False, 'error': err}

            deploy_id = deploy.get('id')
            log(f'Deploy triggered: {deploy_id}', 'success')

            # STEP 7: Poll deployment status
            log('Waiting for deployment to finish (up to 5 minutes)...', 'info')
            live_url = self._wait_for_deploy(deploy_id, project.get('name'), on_log=log)

            if not live_url:
                log('Deployment timeout - check Vercel dashboard', 'warning')
                return {
                    'success': True,
                    'status': 'pending',
                    'live_url': f'https://vercel.com/{project.get("name")}',
                    'message': 'Deployment running. Check Vercel dashboard for status.',
                }

            log(f'Deployment live at: {live_url}', 'success')

            return {
                'success': True,
                'status': 'deployed',
                'live_url': live_url,
                'project_name': project.get('name'),
                'repo': f'{owner}/{repo}',
                'stack': stack,
                'deploy_type': deploy_type,
                'timestamp': datetime.now().isoformat(),
            }

        finally:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    # ============================================
    # Helpers
    # ============================================
    def _sanitize_vercel_name(self, name: str) -> str:
        """Sanitize a name to be a valid Vercel project name."""
        name = name.lower()
        name = re.sub(r'[^a-z0-9._\-]', '-', name)
        name = re.sub(r'-{2,}', '-', name)
        name = name.strip('-.')
        name = name[:100]
        if not name:
            name = 'devops-app'
        return name

    def _parse_github_url(self, url: str) -> Optional[tuple]:
        """Extract (owner, repo) from a GitHub URL."""
        patterns = [
            r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/\s\.]+?)(?:\.git)?$',
        ]
        for p in patterns:
            m = re.match(p, url.strip())
            if m:
                return m.group(1), m.group(2)
        return None

    def _get_repo_info(self, owner: str, repo: str) -> Optional[Dict]:
        """Fetch repo metadata from GitHub API."""
        if not self.github_token:
            print("ERROR _get_repo_info: GITHUB_TOKEN is empty")
            return None

        try:
            url = f'https://api.github.com/repos/{owner}/{repo}'
            print(f"GET {url}")

            resp = requests.get(
                url,
                headers={
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            print(f"Response status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Repo found: {data.get('full_name')}")
                return data

            print(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
            return None

        except Exception as e:
            print(f"_get_repo_info exception: {type(e).__name__}: {e}")
            return None

    def _get_github_repo_id(self, owner: str, repo: str) -> Optional[int]:
        """Fetch the numeric GitHub repo ID (fallback method)."""
        try:
            resp = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers={
                    'Authorization': f'token {self.github_token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get('id')
            print(f"Failed to fetch repo ID: {resp.status_code}")
            return None
        except Exception as e:
            print(f"_get_github_repo_id error: {e}")
            return None

    def _detect_stack(self, path: str) -> Dict[str, Any]:
        """Detect project type from files. Scans root + subfolders (monorepo support)."""
        p = Path(path)
        files = {f.name for f in p.iterdir() if f.is_file()}
        dirs = {d.name for d in p.iterdir() if d.is_dir()}

        # Direct match at root
        result = self._detect_stack_in_dir(p, files)
        if result['type'] != 'unknown':
            return result

        # Monorepo: scan frontend-ish subfolders first
        for subfolder in ['frontend', 'client', 'web', 'app', 'ui']:
            if subfolder in dirs:
                sub_path = p / subfolder
                sub_files = {f.name for f in sub_path.iterdir() if f.is_file()}
                sub_result = self._detect_stack_in_dir(sub_path, sub_files)
                if sub_result['type'] != 'unknown':
                    sub_result['root_dir'] = subfolder
                    print(f"Detected stack in subfolder: {subfolder}")
                    return sub_result

        # Backend-only fallback
        for subfolder in ['backend', 'server', 'api']:
            if subfolder in dirs:
                sub_path = p / subfolder
                sub_files = {f.name for f in sub_path.iterdir() if f.is_file()}
                sub_result = self._detect_stack_in_dir(sub_path, sub_files)
                if sub_result['type'] != 'unknown':
                    sub_result['root_dir'] = subfolder
                    print(f"Detected backend stack in subfolder: {subfolder}")
                    return sub_result

        return {'type': 'unknown', 'framework': 'unknown'}

    def _detect_stack_in_dir(self, p: Path, files: set) -> Dict[str, Any]:
        """Detect stack in a specific directory."""
        if 'package.json' in files:
            framework = 'node'
            try:
                import json
                pkg = json.loads((p / 'package.json').read_text(encoding='utf-8', errors='ignore'))
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'next' in deps:
                    framework = 'nextjs'
                elif 'react' in deps:
                    framework = 'react'
                elif 'vue' in deps:
                    framework = 'vue'
                elif 'svelte' in deps:
                    framework = 'svelte'
                elif 'express' in deps:
                    framework = 'express'
            except Exception:
                pass
            return {'type': 'node', 'framework': framework}

        if 'requirements.txt' in files or 'pyproject.toml' in files or 'setup.py' in files:
            framework = 'python'
            if 'manage.py' in files:
                framework = 'django'
            return {'type': 'python', 'framework': framework}

        if 'index.html' in files:
            return {'type': 'static', 'framework': 'html'}

        if 'go.mod' in files:
            return {'type': 'go', 'framework': 'go'}

        if 'Dockerfile' in files:
            return {'type': 'docker', 'framework': 'unknown'}

        return {'type': 'unknown', 'framework': 'unknown'}

    def _create_vercel_project(self, name: str, owner: str, repo: str, root_dir: Optional[str] = None) -> Dict[str, Any]:
        """Create a Vercel project. rootDirectory is set HERE."""
        try:
            print(f"Creating Vercel project: {name} (root: {root_dir or 'auto'})")

            body = {
                'name': name,
                'framework': None,
            }
            # ⭐ rootDirectory IS set here (on the PROJECT)
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

            print(f"Vercel project response: {resp.status_code}")

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id'), 'name': data.get('name')}

            # Project already exists - fetch it
            if resp.status_code == 409 or 'already exists' in resp.text.lower():
                print("Project exists, fetching...")
                get_resp = requests.get(
                    f'https://api.vercel.com/v9/projects/{name}',
                    headers={'Authorization': f'Bearer {self.vercel_token}'},
                    timeout=15,
                )
                if get_resp.status_code == 200:
                    data = get_resp.json()
                    return {'success': True, 'id': data.get('id'), 'name': data.get('name')}

            return {
                'success': False,
                'error': f'Vercel API {resp.status_code}: {resp.text[:300]}',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _trigger_vercel_deploy(self, project_id: str, owner: str, repo: str, branch: str, repo_id: Optional[int] = None) -> Dict[str, Any]:
        """Trigger a deployment. NOTE: rootDirectory is NOT allowed here."""
        try:
            print(f"Triggering deploy for project {project_id}...")

            if not repo_id:
                repo_id = self._get_github_repo_id(owner, repo)
            if not repo_id:
                return {
                    'success': False,
                    'error': f'Could not fetch GitHub repo ID for {owner}/{repo}'
                }

            print(f"GitHub repo ID: {repo_id}")

            # ⭐ NO rootDirectory here - Vercel API v13 doesn't allow it
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

            print(f"Vercel deploy response: {resp.status_code}")

            if resp.status_code in (200, 201):
                data = resp.json()
                return {'success': True, 'id': data.get('id'), 'url': data.get('url')}

            return {
                'success': False,
                'error': f'Vercel deploy {resp.status_code}: {resp.text[:300]}',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _wait_for_deploy(self, deploy_id: str, project_name: str, timeout: int = 300, on_log=None) -> Optional[str]:
        """Poll deployment status until READY or timeout."""
        start = time.time()
        check_interval = 5
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
                        return f'https://{url}'
                    elif state in ('ERROR', 'error', 'CANCELED'):
                        if on_log:
                            on_log(f'Deployment failed with state: {state}', 'error')
                        return None

            except Exception as e:
                print(f"Poll error: {e}")

            time.sleep(check_interval)

        return None