"""
UniversalDeployer — Agent-Powered Deploy with Auto-Fix
========================================================
Universal language detection + build auto-fix + URL verification.
Handles monorepos where build happens in subfolders.
"""

import os
import re
import sys
import json
import time
import shutil
import random
import string
import subprocess
import tempfile
import requests
from typing import Dict, Any, Optional


class UniversalDeployer:
    """Universal deploy engine with agent-powered fixes."""

    def __init__(self, agent=None):
        self.agent = agent
        self.vercel_token = os.getenv('VERCEL_TOKEN')
        self.netlify_token = os.getenv('NETLIFY_TOKEN')
        self.render_api_key = os.getenv('RENDER_API_KEY')
        self.render_owner_id = os.getenv('RENDER_OWNER_ID')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.temp_root = os.path.join(tempfile.gettempdir(), 'universal_deploy')
        os.makedirs(self.temp_root, exist_ok=True)

    # ============================================
    # HELPERS
    # ============================================
    def _suffix(self, n=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

    def _safe_name(self, repo, max_len=30):
        name = re.sub(r'[^a-z0-9\-]', '-', repo.lower())
        name = re.sub(r'-+', '-', name).strip('-')
        return name[:max_len] or 'app'

    def _run_stream(self, cmd, cwd, log, timeout=900, env=None):
        """Run command with streaming output."""
        try:
            log(f"   ▶️  {cmd[:100]}")
            proc = subprocess.Popen(
                cmd, cwd=cwd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                env=env or os.environ.copy(),
                encoding='utf-8', errors='replace',
            )
            lines = []
            last_hb = time.time()
            start = time.time()

            for line in iter(proc.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                lines.append(line)

                if time.time() - last_hb > 15:
                    log(f"      ⏳ {time.time()-start:.0f}s...")
                    last_hb = time.time()

                low = line.lower()
                if any(k in low for k in [
                    'error', 'fail', 'warn', 'added', 'removed',
                    'compil', 'build', 'done', 'success', 'ready',
                ]):
                    log(f"      {line[:200]}")
                    last_hb = time.time()

                if time.time() - start > timeout:
                    proc.kill()
                    return False, '\n'.join(lines[-50:])

            proc.wait(timeout=60)
            return proc.returncode == 0, '\n'.join(lines[-100:])
        except Exception as e:
            return False, str(e)[:200]

    def _clone_repo(self, owner, repo, branch, log):
        """Clone repo to temp folder."""
        deploy_id = f"{owner}-{repo}-{self._suffix()}"
        target = os.path.join(self.temp_root, deploy_id)

        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)

        token = self.github_token
        clone_url = f'https://{token}@github.com/{owner}/{repo}.git' if token else f'https://github.com/{owner}/{repo}.git'

        log(f"   📥 Cloning {owner}/{repo}...")
        try:
            r = subprocess.run(
                ['git', 'clone', '--depth', '1', '--single-branch', '-b', branch, clone_url, target],
                capture_output=True, text=True, timeout=180,
            )
            if r.returncode != 0:
                return None, f'Clone failed: {r.stderr[:200]}'
            log(f"   ✅ Cloned")
            return target, None
        except Exception as e:
            return None, str(e)[:200]

    # ============================================
    # LANGUAGE DETECTION
    # ============================================
    def detect_language(self, repo_path):
        """Detect language + framework + build config."""
        result = {
            'language': 'unknown',
            'framework': 'unknown',
            'frontend_dir': None,
            'backend_dir': None,
            'build_cmd': '',
            'output_dir': '',
            'node_version': '20',
            'has_frontend': False,
            'has_backend': False,
            'backend_lang': 'unknown',
        }

        # Frontend detection
        for cand in ['.', 'frontend', 'client', 'web', 'ui', 'app']:
            p = repo_path if cand == '.' else os.path.join(repo_path, cand)
            pkg = os.path.join(p, 'package.json')

            if os.path.exists(pkg):
                result['frontend_dir'] = cand if cand != '.' else '.'
                result['has_frontend'] = True

                try:
                    with open(pkg) as f:
                        data = json.load(f)

                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

                    if 'next' in deps:
                        result['framework'] = 'next'
                        result['output_dir'] = '.next'
                    elif 'vite' in deps:
                        result['framework'] = 'vite'
                        result['output_dir'] = 'dist'
                    elif 'react-scripts' in deps or 'react' in deps:
                        result['framework'] = 'react'
                        result['output_dir'] = 'build'
                    elif 'vue' in deps:
                        result['framework'] = 'vue'
                        result['output_dir'] = 'dist'
                    elif 'angular' in deps:
                        result['framework'] = 'angular'
                        result['output_dir'] = 'dist'
                    elif 'svelte' in deps:
                        result['framework'] = 'svelte'
                        result['output_dir'] = 'build'
                    else:
                        result['framework'] = 'node'
                        result['output_dir'] = 'build'

                    result['build_cmd'] = 'npm run build'
                    result['language'] = 'node'

                    engines = data.get('engines', {})
                    if 'node' in engines:
                        v = re.sub(r'[^0-9]', '', str(engines['node']))[:2]
                        if v:
                            result['node_version'] = v

                except Exception:
                    pass
                break

        # Backend detection
        for bdir in ['backend', 'server', 'api']:
            bp = os.path.join(repo_path, bdir)

            if not os.path.isdir(bp):
                continue

            if os.path.exists(os.path.join(bp, 'requirements.txt')):
                result['backend_dir'] = bdir
                result['has_backend'] = True
                result['backend_lang'] = 'python'
                if result['language'] == 'unknown':
                    result['language'] = 'python'
                break
            if os.path.exists(os.path.join(bp, 'package.json')):
                result['backend_dir'] = bdir
                result['has_backend'] = True
                result['backend_lang'] = 'node'
                if result['language'] == 'unknown':
                    result['language'] = 'node'
                break
            if os.path.exists(os.path.join(bp, 'go.mod')):
                result['backend_dir'] = bdir
                result['has_backend'] = True
                result['backend_lang'] = 'go'
                if result['language'] == 'unknown':
                    result['language'] = 'go'
                break

        # Static HTML
        if result['language'] == 'unknown':
            if os.path.exists(os.path.join(repo_path, 'index.html')):
                result['language'] = 'static'
                result['framework'] = 'static'
                result['output_dir'] = '.'
                result['has_frontend'] = True
                result['frontend_dir'] = '.'

        return result

    # ============================================
    # FIND BUILD FOLDER (SMART SEARCH)
    # ============================================
    def _find_build_folder(self, repo_path, log):
        """
        Smart build folder detection.
        Handles monorepos where build happens in subfolders.

        Checks:
        - repo/frontend/build
        - repo/client/build
        - repo/web/build
        - repo/build
        - repo/frontend/dist
        - repo/dist
        - DEEP SEARCH (any folder with index.html + static/assets)
        """
        # Priority locations
        priority = [
            'frontend/build',
            'client/build',
            'web/build',
            'build',
            'frontend/dist',
            'client/dist',
            'web/dist',
            'dist',
            'frontend/out',
            'out',
        ]

        for rel in priority:
            p = os.path.join(repo_path, rel)

            if not os.path.isdir(p):
                continue

            index = os.path.join(p, 'index.html')

            if not os.path.exists(index):
                continue

            try:
                files = os.listdir(p)
                has_static = 'static' in files or 'assets' in files

                if has_static:
                    log(f"   ✅ Found build: {rel}")
                    return p
                else:
                    log(f"   ⚠️ {rel}/ has index.html but no assets — skipping")
            except Exception:
                pass

        # Deep recursive search
        log(f"   🔍 Deep searching for build output...")

        def search_dir(path, depth=0):
            if depth > 5:
                return None

            try:
                entries = os.listdir(path)
            except Exception:
                return None

            # Skip certain folders
            skip = {'node_modules', '.git', '.cache', '.next', 'public', 'src'}

            for entry in entries:
                if entry in skip:
                    continue

                full = os.path.join(path, entry)

                if not os.path.isdir(full):
                    continue

                # Check if this folder is build output
                if os.path.exists(os.path.join(full, 'index.html')):
                    try:
                        sub = os.listdir(full)
                        if 'static' in sub or 'assets' in sub:
                            log(f"   ✅ Found build (deep): {os.path.relpath(full, repo_path)}")
                            return full
                    except Exception:
                        pass

                # Recurse
                result = search_dir(full, depth + 1)
                if result:
                    return result

            return None

        return search_dir(repo_path)

    # ============================================
    # AUTO-FIX PACKAGE.JSON
    # ============================================
    def auto_fix_package_json(self, frontend_path, log):
        """Auto-fix common package.json issues."""
        pkg_path = os.path.join(frontend_path, 'package.json')

        if not os.path.exists(pkg_path):
            return False

        try:
            with open(pkg_path) as f:
                pkg = json.load(f)

            modified = False
            scripts = pkg.setdefault('scripts', {})

            if 'build' not in scripts:
                scripts['build'] = 'react-scripts build'
                modified = True
                log(f"   🔧 Added missing 'build' script")

            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            if 'react-scripts' in deps or 'react' in deps:
                if pkg.get('homepage') != '.':
                    pkg['homepage'] = '.'
                    modified = True
                    log(f"   🔧 Fixed homepage → '.'")

            if modified:
                with open(pkg_path, 'w') as f:
                    json.dump(pkg, f, indent=2)

            return modified
        except Exception as e:
            log(f"   ⚠️ package.json fix: {str(e)[:100]}")
            return False

    # ============================================
    # BUILD WITH AUTO-FIX
    # ============================================
    def build_with_fix(self, frontend_path, output, log, max_attempts=3):
        """Build frontend with auto-fix + smart build folder detection."""
        for attempt in range(1, max_attempts + 1):
            log(f"   🔨 Build attempt {attempt}/{max_attempts}...")

            # npm install
            log(f"   📦 npm install...")
            ok, out = self._run_stream(
                'npm install --no-audit --no-fund --legacy-peer-deps',
                frontend_path, log, timeout=900,
            )

            if not ok:
                log(f"   ⚠️ Retry without legacy-peer-deps...")
                ok, out = self._run_stream(
                    'npm install --no-audit --no-fund',
                    frontend_path, log, timeout=900,
                )
                if not ok:
                    if attempt < max_attempts:
                        log(f"   🩺 Auto-fix attempt...")
                        self._auto_fix_build(frontend_path, out, log)
                        continue
                    return None, f'npm install failed: {out[-300:]}'

            # npm run build
            log(f"   🔨 npm run build...")
            env = os.environ.copy()
            env['NODE_OPTIONS'] = '--max-old-space-size=4096'
            env['CI'] = 'false'
            env['GENERATE_SOURCEMAP'] = 'false'
            env['DISABLE_ESLINT_PLUGIN'] = 'true'
            env['TSC_COMPILE_ON_ERROR'] = 'true'

            ok, out = self._run_stream('npm run build', frontend_path, log, timeout=900, env=env)

            # ⭐ SMART: Search build output in repo (not just frontend_path)
            # Need repo root — try current + parent
            search_roots = [frontend_path]

            # If frontend_path is subfolder, also try repo root
            parent = os.path.dirname(frontend_path)
            if parent and parent != frontend_path:
                search_roots.append(parent)

            build_path = None
            for root in search_roots:
                build_path = self._find_build_folder(root, log)
                if build_path:
                    break

            if build_path:
                # Add _redirects
                try:
                    with open(os.path.join(build_path, '_redirects'), 'w', newline='\n') as f:
                        f.write('/*    /index.html   200\n')
                    log(f"   ✅ Added _redirects")
                except Exception:
                    pass

                return build_path, None

            log(f"   ⚠️ Build folder not found (attempt {attempt})")

            if attempt >= max_attempts:
                # Show what's inside for debug
                log(f"   📁 Repo contents:")
                try:
                    for item in os.listdir(frontend_path):
                        log(f"      - {item}")
                except Exception:
                    pass
                return None, f'Build output not found after {max_attempts} attempts'

            log(f"   🩺 Auto-fix attempt {attempt}...")
            self._auto_fix_build(frontend_path, out, log)
            time.sleep(2)

        return None, 'Build failed'

    def _auto_fix_build(self, frontend_path, error_output, log):
        """Auto-fix build errors via HealerAgent + common fixes."""
        try:
            # Try HealerAgent
            if self.agent:
                try:
                    from .healer_agent import HealerAgent
                except ImportError:
                    try:
                        from agents.specialists.healer_agent import HealerAgent
                    except ImportError:
                        HealerAgent = None

                if HealerAgent:
                    healer = HealerAgent()

                    pkg_content = ''
                    try:
                        with open(os.path.join(frontend_path, 'package.json')) as f:
                            pkg_content = f.read()
                    except Exception:
                        pass

                    result = healer.process({
                        'action': 'fix_code',
                        'code': pkg_content,
                        'error': error_output[-2000:],
                        'language': 'json',
                    })

                    if isinstance(result, dict) and result.get('success'):
                        log(f"   ✅ HealerAgent fixed")
                        return True

            # Common fixes
            log(f"   🔧 Common fixes...")

            try:
                plock = os.path.join(frontend_path, 'package-lock.json')
                if os.path.exists(plock):
                    os.remove(plock)
                    log(f"   🔧 Removed package-lock.json")

                nm = os.path.join(frontend_path, 'node_modules')
                if os.path.exists(nm):
                    shutil.rmtree(nm, ignore_errors=True)
                    log(f"   🔧 Removed node_modules")
            except Exception:
                pass

            common_deps = {
                'react-scripts': '^5.0.1',
                'web-vitals': '^2.1.4',
            }

            try:
                pkg_path = os.path.join(frontend_path, 'package.json')
                with open(pkg_path) as f:
                    pkg = json.load(f)

                deps = pkg.setdefault('dependencies', {})
                for dep, version in common_deps.items():
                    if dep not in deps:
                        deps[dep] = version

                with open(pkg_path, 'w') as f:
                    json.dump(pkg, f, indent=2)

                log(f"   🔧 Added common deps")
            except Exception:
                pass

            return True
        except Exception as e:
            log(f"   ⚠️ Auto-fix error: {str(e)[:150]}")
            return False

    # ============================================
    # URL VERIFY
    # ============================================
    def verify_url(self, url, log, timeout=180):
        """Verify URL returns 200."""
        start = time.time()
        last_code = None

        while time.time() - start < timeout:
            try:
                r = requests.get(url, timeout=10, allow_redirects=True)
                code = r.status_code

                if code != last_code:
                    log(f"   📊 URL check: {code}")
                    last_code = code

                if code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                if last_code != 'DNS':
                    log(f"   ⏳ DNS propagating...")
                    last_code = 'DNS'
            except Exception:
                pass

            time.sleep(8)

        return False

    # ============================================
    # MAIN DEPLOY
    # ============================================
    def deploy(self, provider, owner, repo, repo_url, default_branch, stack_info, sid=None, on_log=None):
        """Main deploy entry point."""
        provider = (provider or '').lower().strip()

        def log(msg, level='info'):
            try:
                print(f"[{provider.upper()}] {msg}", flush=True)
            except Exception:
                pass
            if on_log:
                try:
                    on_log(msg, level)
                except Exception:
                    pass

        log("=" * 60)
        log(f"🚀 {provider.upper()} Deploy: {owner}/{repo}")
        log("=" * 60)

        repo_path, err = self._clone_repo(owner, repo, default_branch, log)
        if not repo_path:
            return {'success': False, 'error': err}

        try:
            info = self.detect_language(repo_path)

            log(f"   🔍 Language: {info['language']}")
            log(f"   🔍 Framework: {info['framework']}")
            log(f"   📁 Frontend: {info.get('frontend_dir') or 'none'}")
            log(f"   📁 Backend: {info.get('backend_dir') or 'none'}")
            log(f"   📁 Output: {info['output_dir']}")

            if provider in ('vercel', 'netlify'):
                if not info['has_frontend']:
                    return {'success': False, 'error': 'No frontend found'}

                frontend_path = repo_path if info['frontend_dir'] == '.' else os.path.join(repo_path, info['frontend_dir'])

                log("")
                log("   🔧 Auto-fixing configs...")
                self.auto_fix_package_json(frontend_path, log)

                log("")
                build_path, err = self.build_with_fix(frontend_path, info['output_dir'], log, max_attempts=3)

                if not build_path:
                    return {'success': False, 'error': f'Build failed: {err}'}

                log("")
                if provider == 'netlify':
                    return self._deploy_netlify_cli(build_path, owner, repo, log)
                else:
                    return self._deploy_vercel_cli(build_path, owner, repo, log)

            elif provider == 'render':
                return self._deploy_render_api(repo_path, owner, repo, default_branch, info, log)

            return {'success': False, 'error': f'Unknown provider: {provider}'}

        finally:
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
            except Exception:
                pass

    # ============================================
    # NETLIFY DEPLOY
    # ============================================
    def _deploy_netlify_cli(self, build_path, owner, repo, log):
        if not self.netlify_token:
            return {'success': False, 'error': 'NETLIFY_TOKEN not set'}

        site_name = f"{self._safe_name(repo)}-{self._suffix(6)}"
        log(f"   📦 Netlify CLI: {site_name}")

        try:
            env = os.environ.copy()
            env['NETLIFY_AUTH_TOKEN'] = self.netlify_token

            cmd = (
                f'npx netlify-cli@latest deploy --prod '
                f'--dir="{build_path}" --site="{site_name}" '
                f'--auth="{self.netlify_token}" --json'
            )

            ok, output = self._run_stream(cmd, build_path, log, timeout=600, env=env)

            url = None
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('{'):
                    try:
                        data = json.loads(line)
                        url = data.get('url') or data.get('deploy_url') or data.get('ssl_url')
                        if url:
                            break
                    except Exception:
                        pass

            if not url:
                m = re.search(r'https://[a-z0-9\-]+\.netlify\.app', output)
                if m:
                    url = m.group(0)

            if not url:
                return {'success': False, 'error': f'No URL: {output[-300:]}'}

            log(f"   ✅ URL: {url}")
            verified = self.verify_url(url, log, timeout=180)

            return {
                'success': True, 'provider': 'netlify',
                'url': url, 'primary_url': url, 'live_url': url,
                'frontend_url': url,
                'frontend_ready': True, 'backend_ready': False,
                'site_name': site_name, 'verified': verified,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)[:300]}

    # ============================================
    # VERCEL DEPLOY
    # ============================================
    def _deploy_vercel_cli(self, build_path, owner, repo, log):
        if not self.vercel_token:
            return {'success': False, 'error': 'VERCEL_TOKEN not set'}

        project_name = f"{self._safe_name(repo)}-{self._suffix(6)}"
        log(f"   📦 Vercel CLI: {project_name}")

        try:
            env = os.environ.copy()
            env['VERCEL_TOKEN'] = self.vercel_token

            cmd = (
                f'npx vercel@latest deploy --prod --yes '
                f'--token="{self.vercel_token}" --name="{project_name}"'
            )

            ok, output = self._run_stream(cmd, build_path, log, timeout=600, env=env)

            url = None
            m = re.search(r'https://[a-z0-9\-]+\.vercel\.app', output)
            if m:
                url = m.group(0)

            if not url:
                return {'success': False, 'error': f'No URL: {output[-300:]}'}

            log(f"   ✅ URL: {url}")
            verified = self.verify_url(url, log, timeout=180)

            return {
                'success': True, 'provider': 'vercel',
                'url': url, 'primary_url': url, 'live_url': url,
                'frontend_url': url,
                'frontend_ready': True, 'backend_ready': False,
                'project_name': project_name, 'verified': verified,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)[:300]}

    # ============================================
    # RENDER DEPLOY
    # ============================================
    def _deploy_render_api(self, repo_path, owner, repo, branch, info, log):
        if not self.render_api_key:
            return {'success': False, 'error': 'RENDER_API_KEY not set'}

        service_name = f"{self._safe_name(repo)}-{self._suffix(6)}"
        backend_dir = info.get('backend_dir') or '.'
        backend_lang = info.get('backend_lang') or 'python'

        if backend_lang == 'python':
            env = 'python'
            build_cmd = 'pip install -r requirements.txt'
            start_cmd = 'gunicorn app:app --bind 0.0.0.0:$PORT'
        elif backend_lang == 'node':
            env = 'node'
            build_cmd = 'npm install'
            start_cmd = 'npm start'
        elif backend_lang == 'go':
            env = 'go'
            build_cmd = 'go build -o app .'
            start_cmd = './app'
        else:
            env = 'python'
            build_cmd = 'pip install -r requirements.txt'
            start_cmd = 'python app.py'

        log(f"   📦 Render: {service_name}")
        log(f"   🐍 {backend_lang}")

        try:
            service_details = {
                'env': env,
                'plan': 'free',
                'region': 'oregon',
                'buildCommand': build_cmd,
                'startCommand': start_cmd,
                'autoDeploy': 'yes',
                'rootDir': backend_dir,
            }

            body = {
                'type': 'web_service',
                'name': service_name,
                'ownerId': self.render_owner_id,
                'repo': f'https://github.com/{owner}/{repo}',
                'branch': branch,
                'autoDeploy': 'yes',
                'serviceDetails': service_details,
            }

            r = requests.post(
                'https://api.render.com/v1/services',
                headers={
                    'Authorization': f'Bearer {self.render_api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                json=body, timeout=30,
            )

            if r.status_code in (409, 422):
                service_name = f"{self._safe_name(repo)}-{self._suffix(12)}"
                body['name'] = service_name
                r = requests.post(
                    'https://api.render.com/v1/services',
                    headers={
                        'Authorization': f'Bearer {self.render_api_key}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    json=body, timeout=30,
                )

            if r.status_code not in (200, 201):
                return {'success': False, 'error': f'Render: {r.text[:300]}'}

            data = r.json()
            service = data.get('service', data)
            service_id = service.get('id')

            log(f"   ✅ Service: {service_id}")

            url = f'https://{service_name}.onrender.com'

            return {
                'success': True, 'provider': 'render',
                'url': url, 'primary_url': url, 'live_url': url,
                'backend_url': url,
                'frontend_ready': False, 'backend_ready': True,
                'service_id': service_id, 'service_name': service_name,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)[:300]}