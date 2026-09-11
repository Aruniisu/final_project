"""
Multi-Provider Deploy Service
Routes deployments to the right provider (Vercel, Render, Kaniko, Buildah).
"""

import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

from services.providers.vercel_provider import VercelProvider
from services.providers.render_provider import RenderProvider
from services.providers.kaniko_provider import KanikoProvider
from services.providers.buildah_provider import BuildahProvider


class MultiDeployService:
    """Orchestrates deployments across multiple providers."""

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(backend_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=True)

        self.providers = {
            'vercel': VercelProvider(),
            'render': RenderProvider(),
            'kaniko': KanikoProvider(),
            'buildah': BuildahProvider(),
        }
        self.github_token = os.getenv('GITHUB_TOKEN')

        print("MultiDeployService initialized")
        print("   Providers: " + str(list(self.providers.keys())))
        print("   GitHub: " + ("SET" if self.github_token else "NOT SET"))

    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url') or payload.get('repoUrl')
        project_name = payload.get('project_name') or payload.get('projectName') or 'my-app'
        user_provider = payload.get('provider')

        def log(msg, level='info'):
            print("[MULTI] " + str(msg))
            if on_log:
                on_log(msg, level)

        # STEP 1: Parse repo
        parsed = self._parse_url(repo_url)
        if not parsed:
            return {'success': False, 'error': 'Invalid GitHub URL: ' + str(repo_url)}

        owner, repo = parsed
        log('Repo: ' + str(owner) + '/' + str(repo), 'success')

        # STEP 2: Fetch repo info + repo ID
        repo_info = self._get_repo_info(owner, repo)
        if not repo_info:
            return {'success': False, 'error': 'Repo ' + str(owner) + '/' + str(repo) + ' not found'}

        repo_id = repo_info.get('id')
        default_branch = repo_info.get('default_branch', 'main')
        log('GitHub repo ID: ' + str(repo_id), 'info')
        log('Default branch: ' + str(default_branch), 'info')

        # STEP 3: Clone repo + detect stack
        tmp_dir = tempfile.mkdtemp(prefix='multi_deploy_')
        try:
            log('Cloning ' + str(owner) + '/' + str(repo) + '@' + str(default_branch) + '...', 'info')
            clone_url = 'https://' + str(self.github_token) + '@github.com/' + str(owner) + '/' + str(repo) + '.git'
            result = subprocess.run(
                ['git', 'clone', '--depth=1', '--branch', default_branch, clone_url, tmp_dir],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {'success': False, 'error': 'Clone failed: ' + result.stderr[:200]}

            log('Cloned to temp dir', 'success')

            stack = self._detect_stack(tmp_dir)
            log('Detected stack: ' + str(stack["type"]) + ' (' + str(stack["framework"]) + ')', 'info')

            root_dir = stack.get('root_dir')
            if root_dir:
                log('Using subfolder: ' + str(root_dir), 'info')

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # STEP 4: Pick provider
        provider_name = user_provider or self._auto_pick_provider(stack)
        log('Selected provider: ' + str(provider_name), 'success')

        provider = self.providers.get(provider_name)
        if not provider:
            return {'success': False, 'error': 'Unknown provider: ' + str(provider_name)}

        # STEP 5: Deploy with auto-fix loop
        common_payload = {
            'repo_url': repo_url,
            'project_name': project_name,
            'repo_id': repo_id,
            'default_branch': default_branch,
            'root_dir': root_dir,
            'stack': stack,
        }

        log('Deploying via ' + str(provider.display_name) + '...', 'info')

        # ⭐ AUTO-FIX LOOP: Try up to 3 times
        max_attempts = 3
        result = None

        for attempt in range(1, max_attempts + 1):
            if attempt == 1:
                log('=== Deploy attempt 1 ===', 'info')
            else:
                log('=== Deploy attempt ' + str(attempt) + ' (after fix) ===', 'info')

            result = provider.deploy(common_payload, on_log=log)

            if result.get('success'):
                if attempt > 1:
                    result['auto_fix_applied'] = True
                    log('Success on attempt ' + str(attempt) + '!', 'success')
                return result

            # Failed - check if we can auto-fix
            if attempt >= max_attempts:
                log('Reached max attempts (' + str(max_attempts) + '). Giving up.', 'error')
                return result

            if provider_name != 'vercel' or not result.get('deploy_id'):
                log('Cannot auto-fix (only Vercel supported currently)', 'warning')
                return result

            log('Deploy attempt ' + str(attempt) + ' failed. Attempting auto-fix...', 'warning')

            fix_result = self._try_auto_fix(
                provider_name=provider_name,
                provider=provider,
                payload=common_payload,
                deploy_id=result.get('deploy_id'),
                on_log=log,
            )

            if not fix_result.get('success'):
                log('Auto-fix attempt ' + str(attempt) + ' failed: ' + str(fix_result.get('error')), 'error')
                return fix_result

            log('Auto-fix attempt ' + str(attempt) + ' succeeded. Re-deploying...', 'success')
            # Loop continues → next iteration will re-deploy

        return result

    # ============================================
    # Helpers
    # ============================================
    def _parse_url(self, url):
        m = re.match(r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$', url.strip())
        return (m.group(1), m.group(2)) if m else None

    def _get_repo_info(self, owner, repo):
        import requests
        import traceback

        if not self.github_token:
            print("[MULTI] ERROR _get_repo_info: GITHUB_TOKEN is empty")
            return None

        try:
            url = 'https://api.github.com/repos/' + str(owner) + '/' + str(repo)
            print("[MULTI] GET " + url)

            r = requests.get(
                url,
                headers={
                    'Authorization': 'token ' + str(self.github_token),
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            print("[MULTI] Response status: " + str(r.status_code))

            if r.status_code == 200:
                data = r.json()
                print("[MULTI] Repo found: " + str(data.get('full_name')) + " (id=" + str(data.get('id')) + ")")
                return data

            print("[MULTI] GitHub API error " + str(r.status_code) + ": " + r.text[:200])
            return None

        except Exception as e:
            print("[MULTI] _get_repo_info exception: " + type(e).__name__ + ": " + str(e))
            traceback.print_exc()
            return None

    def _detect_stack(self, path):
        p = Path(path)
        files = {f.name for f in p.iterdir() if f.is_file()}
        dirs = {d.name for d in p.iterdir() if d.is_dir()}

        result = self._detect_in_dir(p, files)
        if result['type'] != 'unknown':
            return result

        for subfolder in ['frontend', 'client', 'web', 'app', 'ui']:
            if subfolder in dirs:
                sub_path = p / subfolder
                sub_files = {f.name for f in sub_path.iterdir() if f.is_file()}
                sub_result = self._detect_in_dir(sub_path, sub_files)
                if sub_result['type'] != 'unknown':
                    sub_result['root_dir'] = subfolder
                    print("[MULTI] Detected stack in subfolder: " + subfolder)
                    return sub_result

        for subfolder in ['backend', 'server', 'api']:
            if subfolder in dirs:
                sub_path = p / subfolder
                sub_files = {f.name for f in sub_path.iterdir() if f.is_file()}
                sub_result = self._detect_in_dir(sub_path, sub_files)
                if sub_result['type'] != 'unknown':
                    sub_result['root_dir'] = subfolder
                    print("[MULTI] Detected backend stack in subfolder: " + subfolder)
                    return sub_result

        return {'type': 'unknown', 'framework': 'unknown'}

    def _detect_in_dir(self, p, files):
        if 'package.json' in files:
            framework = 'node'
            try:
                import json
                pkg = json.loads((p / 'package.json').read_text(encoding='utf-8', errors='ignore'))
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'next' in deps: framework = 'nextjs'
                elif 'react' in deps: framework = 'react'
                elif 'vue' in deps: framework = 'vue'
                elif 'svelte' in deps: framework = 'svelte'
                elif 'express' in deps: framework = 'express'
            except Exception:
                pass
            return {'type': 'node', 'framework': framework}

        if 'requirements.txt' in files or 'pyproject.toml' in files or 'setup.py' in files:
            framework = 'python'
            if 'manage.py' in files: framework = 'django'
            return {'type': 'python', 'framework': framework}

        if 'index.html' in files:
            return {'type': 'static', 'framework': 'html'}

        if 'go.mod' in files:
            return {'type': 'go', 'framework': 'go'}

        if 'Dockerfile' in files:
            return {'type': 'docker', 'framework': 'unknown'}

        return {'type': 'unknown', 'framework': 'unknown'}

    def _auto_pick_provider(self, stack):
        stype = stack.get('type')
        if stype in ('node', 'static'):
            return 'vercel'
        if stype == 'python':
            return 'render'
        if stype == 'docker':
            if os.getenv('KUBECONFIG_PATH') and os.path.exists(os.getenv('KUBECONFIG_PATH', '')):
                return 'kaniko'
            return 'buildah'
        return 'vercel'

    # ============================================
    # AUTO-FIX on failure
    # ============================================
    def _try_auto_fix(self, provider_name, provider, payload, deploy_id, on_log):
        """Try to auto-fix a failed deployment."""
        import traceback

        try:
            on_log('=== AUTO-FIX STARTED ===', 'info')
            on_log('Deploy ID: ' + str(deploy_id), 'info')

            from services.auto_fix_service import AutoFixService
            on_log('AutoFixService imported', 'success')

            fixer = AutoFixService()
            on_log('AutoFixService initialized', 'success')

            owner, repo = self._parse_url(payload['repo_url'])
            on_log('Analyzing ' + str(owner) + '/' + str(repo) + '...', 'info')

            fix_result = fixer.analyze_and_fix(
                deploy_id=deploy_id,
                owner=owner,
                repo=repo,
                root_dir=payload.get('root_dir'),
                on_log=on_log,
            )

            if not fix_result.get('success'):
                on_log('Auto-fix failed: ' + str(fix_result.get('error')), 'error')
                return {'success': False, 'error': fix_result.get('error', 'Auto-fix failed')}

            on_log('Fix applied: ' + str(fix_result.get('fix_description')), 'success')

            return {
                'success': True,
                'fix_description': fix_result.get('fix_description'),
                'files_changed': fix_result.get('files_changed', []),
                'commit_sha': fix_result.get('commit_sha'),
            }

        except Exception as e:
            print("=" * 60)
            print("ERROR in _try_auto_fix")
            print("Type: " + type(e).__name__)
            print("Message: " + str(e))
            traceback.print_exc()
            print("=" * 60)

            on_log('Auto-fix error: ' + str(e)[:200], 'error')
            return {'success': False, 'error': 'Auto-fix error: ' + str(e)}