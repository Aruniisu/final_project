"""
SelfHostService - Universal Multi-Framework Deployment Platform
================================================================
Supports: Next.js, React, Vue, Nuxt, Angular, Svelte, Static HTML,
          Flask, Django, FastAPI, Express, Nest, Go, Rust, PHP, Java, Ruby

Features:
- Real-time log streaming (every line + heartbeat)
- MOVE-based cache (instant, not copy)
- Junction-based restore (0s, no copy)
- Repo-based cache key (100% hit rate)
- Cloudflare Tunnel (primary) -> localhost (fallback)
- Auto-restore ALL (proxy + backend + tunnel) on startup
- Thread-safe registry
- Auto-cleanup + Graceful shutdown
- Framework-aware serving (Next.js, Vite, CRA, Nuxt, Angular, etc.)
- Auto-fix npm EINTEGRITY / cache corruption with retry
- UTF-8 safe file writing (Windows-compatible)
- MULTI-TENANT PORT ISOLATION (unique port per deployment)
- AUTO-KILL previous deployment with same slug (no conflicts)
- AUTO-START PROXY (reliable background process)
- AUTO-RESTART CLOUDFLARED with verification
- ⭐ NEW: ANY .html file detection + auto-rename to index.html
"""

import os
import re
import sys
import json
import time
import atexit
import shutil
import hashlib
import socket
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List


# Windows DETACHED flags for persistent tunnels
if os.name == 'nt':
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NO_WINDOW = 0x08000000
    DETACHED_FLAGS = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    PROXY_FLAGS = CREATE_NEW_PROCESS_GROUP
else:
    DETACHED_FLAGS = 0
    PROXY_FLAGS = 0


_REGISTRY_LOCK = threading.Lock()


class SelfHostService:
    """Universal self-hosted deployment service with multi-tenant port isolation."""

    LANG_PATTERNS = {
        'python': ['requirements.txt', 'pyproject.toml', 'Pipfile', 'setup.py', 'manage.py'],
        'node': ['package.json'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml'],
        'php': ['composer.json', 'index.php'],
        'java': ['pom.xml', 'build.gradle'],
        'ruby': ['Gemfile', 'Gemfile.lock'],
        'static': ['index.html'],
    }

    TIMEOUT_INSTALL = 1200
    TIMEOUT_BUILD = 1200
    TIMEOUT_VENV = 300
    TIMEOUT_PIP = 600
    TIMEOUT_GIT = 120

    ENABLE_NODE_CACHE = True
    ENABLE_VENV_CACHE = True
    USE_JUNCTION = True
    USE_MOVE_CACHE = True

    MAX_INSTALL_RETRIES = 2
    MAX_BUILD_RETRIES = 1

    PORTS_PER_DEPLOY = 10
    PORT_RANGE_SIZE = 1000

    def __init__(self, agent=None):
        self.agent = agent
        self.deploy_root = os.getenv('SELF_HOST_ROOT', 'D:/dev/final_project/deployments')
        self.cache_root = os.path.join(self.deploy_root, '_cache')
        self.public_domain = os.getenv('PUBLIC_DOMAIN', 'smartdevops.site')
        self.port_start = int(os.getenv('SELF_HOST_PORT_START', '8000'))
        self.registry_file = os.path.join(self.deploy_root, '_registry.json')

        self.cf_token = os.getenv('CLOUDFLARE_API_TOKEN', '')
        self.cf_zone = os.getenv('CLOUDFLARE_ZONE_ID', '')
        self.cf_tunnel_id = os.getenv(
            'CLOUDFLARE_TUNNEL_ID',
            '768b9df6-6a35-422b-9898-b3f250ef3a1b'
        )
        self.cf_tunnel_name = os.getenv('CLOUDFLARE_TUNNEL_NAME', 'smartdevops-tunnel')
        self.base_domain = os.getenv('CLOUDFLARE_BASE_DOMAIN', 'smartdevops.site')

        os.makedirs(self.deploy_root, exist_ok=True)
        os.makedirs(self.cache_root, exist_ok=True)

        self.active_processes = {}
        self._tunnel_procs = {}

        self._restore_tunnel_procs_from_disk()

        try:
            atexit.register(self.shutdown)
        except Exception:
            pass

    # ============================================
    # RESTORE TUNNEL INFO FROM DISK
    # ============================================
    def _restore_tunnel_procs_from_disk(self):
        try:
            if not os.path.isdir(self.deploy_root):
                return
            for folder in os.listdir(self.deploy_root):
                if folder.startswith('_'):
                    continue
                info_file = os.path.join(self.deploy_root, folder, 'tunnel.json')
                if not os.path.exists(info_file):
                    continue
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    pid = info.get('pid')
                    url = info.get('url')
                    if pid:
                        try:
                            result = subprocess.run(
                                f'tasklist /FI "PID eq {pid}" /NH',
                                shell=True, capture_output=True, text=True, timeout=5,
                            )
                            alive = str(pid) in result.stdout
                        except Exception:
                            alive = False
                        if alive:
                            self._tunnel_procs[folder] = {
                                'pid': pid, 'url': url, 'restored': True,
                            }
                except Exception:
                    pass
        except Exception as e:
            print(f"[SELF-HOST] Restore tunnel procs error: {e}")

    # ============================================
    # GRACEFUL SHUTDOWN
    # ============================================
    def shutdown(self):
        print("[SELF-HOST] Shutdown: cleaning up...")
        killed = 0

        for deploy_id, tunnel in list(self._tunnel_procs.items()):
            try:
                if hasattr(tunnel, 'poll'):
                    if tunnel.poll() is None:
                        tunnel.terminate()
                        killed += 1
                    continue
                if isinstance(tunnel, dict):
                    pid = tunnel.get('pid')
                    if pid:
                        subprocess.run(
                            f'taskkill /F /PID {pid}',
                            shell=True, capture_output=True, timeout=5,
                        )
                        killed += 1
            except Exception as e:
                print(f"[SELF-HOST] Kill {deploy_id}: {e}")

        self._tunnel_procs.clear()

        for deploy_id, procs in list(self.active_processes.items()):
            try:
                for proc_type, proc in procs.items():
                    if proc and hasattr(proc, 'poll') and proc.poll() is None:
                        try:
                            proc.terminate()
                            killed += 1
                        except Exception:
                            pass
            except Exception:
                pass

        self.active_processes.clear()
        print(f"[SELF-HOST] Shutdown complete - killed {killed}")

    # ============================================
    # SLUG HELPER
    # ============================================
    def _slug_from_repo(self, owner, repo):
        owner_part = (owner or '').lower().replace('_', '-').replace('.', '-')
        repo_part = (repo or '').lower().replace('_', '-').replace('.', '-')
        slug = f"{owner_part}-{repo_part}"
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')[:60]
        return slug or 'app'

    # ============================================
    # PORT ALLOCATION (Multi-Tenant)
    # ============================================
    def _port_listening(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                return s.connect_ex(('127.0.0.1', port)) == 0
        except Exception:
            return False

    def _find_free_port(self, start=None):
        if start is None:
            start = self.port_start

        for port in range(start, start + self.PORT_RANGE_SIZE):
            if self._port_listening(port):
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('127.0.0.1', port))
                    s.close()
                time.sleep(0.05)
                if not self._port_listening(port):
                    return port
            except OSError:
                continue

        raise RuntimeError(f'No free port in range {start}-{start + self.PORT_RANGE_SIZE}')

    def _get_deploy_port_base(self, deploy_id):
        hash_hex = hashlib.md5(deploy_id.encode()).hexdigest()
        hash_int = int(hash_hex[:8], 16)
        num_blocks = self.PORT_RANGE_SIZE // self.PORTS_PER_DEPLOY
        offset = (hash_int % num_blocks) * self.PORTS_PER_DEPLOY
        return self.port_start + offset

    def _kill_previous_deployment(self, slug, log):
        try:
            registry = self.list_deployments()
            killed = []

            for existing_id, existing_data in list(registry.items()):
                existing_owner = existing_data.get('owner', '')
                existing_repo = existing_data.get('repo', '')
                existing_slug = self._slug_from_repo(existing_owner, existing_repo)

                if existing_slug == slug:
                    log(f"   [Cleanup] Found existing deployment: {existing_id}")
                    self.stop_deployment(existing_id)
                    killed.append(existing_id)

                    proxy_port = existing_data.get('proxy_port')
                    backend_port = existing_data.get('backend_port')

                    for port in [proxy_port, backend_port]:
                        if not port:
                            continue
                        try:
                            result = subprocess.run(
                                f'netstat -ano | findstr :{port}',
                                shell=True, capture_output=True, text=True, timeout=5,
                            )
                            if result.stdout:
                                for line in result.stdout.splitlines():
                                    if 'LISTENING' in line:
                                        parts = line.split()
                                        if len(parts) >= 5:
                                            pid = parts[-1]
                                            subprocess.run(
                                                f'taskkill /F /PID {pid}',
                                                shell=True, capture_output=True, timeout=5,
                                            )
                        except Exception:
                            pass

            if killed:
                log(f"   [Cleanup] Killed {len(killed)} previous deployment(s)")

        except Exception as e:
            log(f"   [Cleanup] Warning: {str(e)[:100]}")

    # ============================================
    # NPM CACHE FIX
    # ============================================
    def _npm_cache_clean(self, log):
        try:
            log("   [Auto-fix] npm cache clean --force")
            subprocess.run('npm cache clean --force', shell=True, capture_output=True, timeout=60)
            log("   [Auto-fix] npm cache verify")
            subprocess.run('npm cache verify', shell=True, capture_output=True, timeout=60)
            log("   [OK] npm cache cleaned")
            return True
        except Exception as e:
            log(f"   [WARN] npm cache clean failed: {str(e)[:100]}")
            return False

    def _clean_node_modules(self, path, log):
        try:
            nm = os.path.join(path, 'node_modules')
            if os.path.exists(nm):
                log("   [Auto-fix] removing node_modules")
                subprocess.run(f'rd /s /q "{nm}"', shell=True, capture_output=True, timeout=120)
                log("   [OK] node_modules removed")
            return True
        except Exception as e:
            log(f"   [WARN] Remove node_modules failed: {str(e)[:100]}")
            return False

    def _is_eintegrity_error(self, output):
        if not output:
            return False
        output_lower = output.lower()
        return (
            'eintegrity' in output_lower
            or 'integrity checksum failed' in output_lower
            or ('tarball data' in output_lower and 'corrupted' in output_lower)
        )

    # ============================================
    # ⭐ NEW: DETECT ANY HTML FILE (any name, not just index.html)
    # ============================================
    def _find_html_entry(self, path):
        """Find any .html file in the given path. Returns (filename, full_path) or (None, None)."""
        try:
            if not os.path.isdir(path):
                return (None, None)
            for f in os.listdir(path):
                if f.lower().endswith('.html') and os.path.isfile(os.path.join(path, f)):
                    return (f, os.path.join(path, f))
        except Exception:
            pass
        return (None, None)

    def _ensure_index_html(self, path, log):
        """
        ⭐ NEW: Ensure 'index.html' exists.
        If not, find ANY .html file and copy it to index.html (keeps original).
        Returns True if index.html exists after this call.
        """
        index_path = os.path.join(path, 'index.html')
        if os.path.exists(index_path):
            return True

        src_name, src_path = self._find_html_entry(path)
        if not src_path:
            return False

        try:
            with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log(f"   [Auto-fix] Renamed '{src_name}' -> 'index.html'")
            return True
        except Exception as e:
            log(f"   [Auto-fix] Rename failed: {str(e)[:100]}")
            try:
                shutil.copy2(src_path, index_path)
                log(f"   [Auto-fix] Copied '{src_name}' -> 'index.html'")
                return True
            except Exception as e2:
                log(f"   [Auto-fix] Copy failed: {str(e2)[:100]}")
                return False

    # ============================================
    # MAIN DEPLOY
    # ============================================
    def deploy(self, owner, repo, repo_url, default_branch, stack_info=None, sid=None, on_log=None):
        def log(msg, level='info'):
            try:
                print(f"[SELF-HOST] {msg}", flush=True)
            except Exception:
                pass
            if on_log:
                try:
                    on_log(msg, level)
                except Exception:
                    pass

        log("=" * 60)
        log(f"Self-Hosting: {owner}/{repo}")
        log("=" * 60)

        slug = self._slug_from_repo(owner, repo)
        log("")
        log(f"Step 0/8: Cleaning up previous '{slug}' deployment")
        self._kill_previous_deployment(slug, log)

        log("")
        log("Step 1/8: Allocating deployment slot")
        deploy_id = self._generate_deploy_id(owner, repo)
        log(f"   Deploy ID: {deploy_id}")

        deploy_dir = os.path.join(self.deploy_root, deploy_id)
        os.makedirs(deploy_dir, exist_ok=True)

        self._save_to_registry(deploy_id, {
            'id': deploy_id, 'owner': owner, 'repo': repo, 'repo_url': repo_url,
            'url': None, 'status': 'deploying',
            'deploy_type': (stack_info or {}).get('deploy_type', 'auto'),
            'frontend_ready': False, 'backend_ready': False,
            'proxy_port': None, 'backend_port': None,
            'deployed_at': time.time(),
        })
        log("   Registry: status=deploying")

        log("")
        log("Step 2/8: Cloning repository")
        repo_dir = os.path.join(deploy_dir, 'repo')

        try:
            clone_url = self._inject_token(repo_url)
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--single-branch',
                 '-b', default_branch, clone_url, repo_dir],
                capture_output=True, text=True, timeout=self.TIMEOUT_GIT,
            )
            if result.returncode != 0:
                self._update_registry_status(deploy_id, 'failed', error='Clone failed')
                return {'success': False, 'error': 'Clone failed'}
            log("   Cloned")
        except Exception as e:
            self._update_registry_status(deploy_id, 'failed', error=str(e)[:200])
            return {'success': False, 'error': f'Clone error: {str(e)[:200]}'}

        log("")
        log("Step 3/8: Detecting structure")
        detection = self._detect_structure(repo_dir)
        log(f"   Detected: {detection['type']}")
        log(f"   Languages: {', '.join(detection['languages'])}")
        if detection.get('frontend'):
            log(f"   Frontend: {detection['frontend']}")
            log(f"   Frontend framework: {detection.get('frontend_framework', 'unknown')}")
        if detection.get('backend'):
            log(f"   Backend: {detection['backend']} ({detection.get('backend_lang', 'unknown')})")

        deploy_type = (stack_info or {}).get('deploy_type', 'auto')
        log(f"   Deploy type: {deploy_type}")

        if deploy_type == 'frontend':
            detection['backend'] = None
        elif deploy_type == 'backend':
            detection['frontend'] = None

        log("")
        log("Step 4/8: Building (parallel)")

        from concurrent.futures import ThreadPoolExecutor

        def build_fe():
            if detection.get('frontend'):
                return self._build_frontend_with_retry(repo_dir, detection['frontend'], log)
            return {'success': False, 'skipped': True}

        def build_be():
            if detection.get('backend'):
                return self._build_backend(repo_dir, detection['backend'],
                                           detection.get('backend_lang', 'unknown'), log)
            return {'success': False, 'skipped': True}

        with ThreadPoolExecutor(max_workers=2) as executor:
            fe_future = executor.submit(build_fe)
            be_future = executor.submit(build_be)
            fe_result = fe_future.result()
            be_result = be_future.result()

        frontend_ready = fe_result.get('success', False)
        frontend_build_path = fe_result.get('build_path')
        frontend_framework = fe_result.get('framework') or detection.get('frontend_framework')
        frontend_serve_mode = fe_result.get('serve_mode', 'static')
        backend_ready = be_result.get('success', False)

        if not frontend_ready and not fe_result.get('skipped'):
            log(f"   Frontend failed: {fe_result.get('error')}")
        if not backend_ready and not be_result.get('skipped'):
            log(f"   Backend failed: {be_result.get('error')}")

        log("")
        log("Step 5/8: Allocating ports (multi-tenant)")
        port_base = self._get_deploy_port_base(deploy_id)
        log(f"   Port base: {port_base} (deployment-specific)")

        proxy_port = self._find_free_port(start=port_base)
        backend_port = self._find_free_port(start=proxy_port + 1)

        log(f"   Ports: proxy={proxy_port}, backend={backend_port}")

        backend_proc = None
        if backend_ready:
            log("")
            log("Step 6/8: Starting backend")
            backend_proc = self._start_backend(
                deploy_id, deploy_dir, repo_dir,
                detection['backend'], detection.get('backend_lang', 'unknown'),
                backend_port, log,
            )

        frontend_proc = None
        frontend_server_port = None
        if frontend_ready and frontend_serve_mode == 'server':
            log("")
            log(f"Step 6b/8: Starting frontend server ({frontend_framework})")
            frontend_proc = self._start_frontend_server(
                deploy_id, deploy_dir, repo_dir,
                detection['frontend'], frontend_framework,
                backend_port, log,
            )
            if frontend_proc:
                frontend_server_port = backend_port
                log(f"   Frontend server listening on port {frontend_server_port}")

        log("")
        log("Step 7/8: Starting reverse proxy")
        proxy_proc = self._start_proxy(
            deploy_id, deploy_dir,
            frontend_ready, frontend_build_path, frontend_serve_mode,
            backend_ready, backend_port, proxy_port,
            frontend_server_port=frontend_server_port,
            log=log,
        )

        log("")
        log("Step 8/8: Generating public URL (Cloudflare)")
        public_url = self._expose_url(deploy_id, proxy_port, log, owner=owner, repo=repo)
        if not public_url:
            public_url = f'http://localhost:{proxy_port}'
            log(f"   Fallback: {public_url}")

        existing = self.get_deployment(deploy_id) or {}
        final_status = 'success' if (frontend_ready or backend_ready) else 'failed'

        self._save_to_registry(deploy_id, {
            **existing,
            'id': deploy_id, 'owner': owner, 'repo': repo, 'repo_url': repo_url,
            'url': public_url, 'deploy_type': deploy_type, 'status': final_status,
            'frontend_ready': frontend_ready, 'backend_ready': backend_ready,
            'proxy_port': proxy_port, 'backend_port': backend_port,
            'frontend_framework': frontend_framework,
            'frontend_serve_mode': frontend_serve_mode,
            'frontend_server_port': frontend_server_port,
            'deployed_at': existing.get('deployed_at', time.time()),
            'completed_at': time.time(),
        })

        self.active_processes[deploy_id] = {
            'backend': backend_proc,
            'frontend': frontend_proc,
            'proxy': proxy_proc,
        }

        both_failed = (not frontend_ready and not backend_ready)

        log("")
        log("=" * 60)
        if both_failed:
            log("DEPLOYMENT FAILED (both frontend & backend)")
        else:
            log("DEPLOYMENT SUCCESSFUL")
            log(f"   URL: {public_url}")
            log(f"   Frontend: {'OK' if frontend_ready else 'FAIL'} ({frontend_framework})")
            log(f"   Backend: {'OK' if backend_ready else 'FAIL'}")
            log(f"   Ports: proxy={proxy_port}, backend={backend_port}")
            if frontend_server_port:
                log(f"   Frontend server: port {frontend_server_port}")
        log("=" * 60)

        if both_failed:
            return {
                'success': False,
                'error': f"Build failed: both frontend and backend failed. Frontend: {fe_result.get('error', 'unknown')}",
                'provider': 'self-host',
                'deploy_id': deploy_id,
                'url': public_url,
                'frontend_ready': False,
                'backend_ready': False,
            }

        return {
            'success': True, 'provider': 'self-host',
            'deploy_id': deploy_id, 'url': public_url,
            'primary_url': public_url, 'live_url': public_url,
            'frontend_url': public_url if frontend_ready else None,
            'backend_url': f'{public_url}/api' if backend_ready else None,
            'deploy_type': deploy_type,
            'frontend_ready': frontend_ready, 'backend_ready': backend_ready,
            'frontend_framework': frontend_framework,
            'proxy_port': proxy_port,
            'backend_port': backend_port,
        }

    # ============================================
    # REAL-TIME STREAMING
    # ============================================
    def _run_streaming(self, cmd, cwd, log, timeout, env=None):
        try:
            display_cmd = cmd[:120] + ('...' if len(cmd) > 120 else '')
            log(f"   > {display_cmd}")

            proc = subprocess.Popen(
                cmd, cwd=cwd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                env=env or os.environ.copy(),
                encoding='utf-8', errors='replace',
            )

            output_lines = []
            start = time.time()
            last_heartbeat = time.time()
            line_count = 0

            try:
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    if not line:
                        continue
                    output_lines.append(line)
                    line_count += 1

                    if time.time() - last_heartbeat > 15:
                        elapsed = time.time() - start
                        log(f"      Still running... {elapsed:.0f}s ({line_count} lines)")
                        last_heartbeat = time.time()

                    lower = line.lower()
                    should_stream = (
                        'error' in lower or 'failed' in lower or 'warn' in lower
                        or 'deprecated' in lower or 'added' in lower or 'removed' in lower
                        or 'installed' in lower or 'audited' in lower
                        or 'compil' in lower or 'bundl' in lower or 'build' in lower
                        or 'optimiz' in lower or 'creating' in lower or 'transform' in lower
                        or 'vite' in lower or 'webpack' in lower or 'rollup' in lower
                        or 'done' in lower or 'success' in lower or 'complete' in lower
                        or 'ready' in lower or 'built' in lower or 'finish' in lower
                        or 'collecting' in lower or 'downloading' in lower
                        or 'installing' in lower or 'building wheel' in lower
                        or 'successfully installed' in lower or 'packages in' in lower
                        or 'next' in lower or 'nuxt' in lower or 'angular' in lower
                    )

                    if should_stream:
                        display = line[:250] if len(line) > 250 else line
                        log(f"      {display}")
                        last_heartbeat = time.time()

                    if time.time() - start > timeout:
                        log(f"   Timeout after {timeout}s")
                        proc.kill()
                        return False, '\n'.join(output_lines[-100:])

            except Exception as e:
                log(f"   Stream error: {str(e)[:100]}")

            try:
                proc.wait(timeout=120)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

            rc = proc.returncode
            elapsed = time.time() - start

            if rc == 0:
                log(f"   Done (exit 0, {elapsed:.1f}s, {line_count} lines)")
            else:
                log(f"   Exit code {rc} ({elapsed:.1f}s)")

            return rc == 0, '\n'.join(output_lines[-100:])

        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            log(f"   Timeout {timeout}s")
            return False, 'timeout'
        except Exception as e:
            log(f"   Exec error: {str(e)[:200]}")
            return False, str(e)

    # ============================================
    # FRONTEND BUILD WITH AUTO-RETRY
    # ============================================
    def _build_frontend_with_retry(self, repo_dir, subdir, log):
        result = self._build_frontend(repo_dir, subdir, log)

        if result.get('success'):
            return result

        error_output = result.get('output', '') or result.get('error', '')
        is_cache_error = self._is_eintegrity_error(error_output)

        if not is_cache_error:
            log("   [WARN] Error is not auto-fixable (not EINTEGRITY)")
            return result

        log("")
        log("=" * 60)
        log("[AUTO-FIX] npm cache corruption detected")
        log("=" * 60)

        for retry in range(1, self.MAX_INSTALL_RETRIES + 1):
            log("")
            log(f"Retry {retry}/{self.MAX_INSTALL_RETRIES}")

            self._npm_cache_clean(log)

            path = repo_dir if subdir == '.' else os.path.join(repo_dir, subdir)
            self._clean_node_modules(path, log)

            try:
                pkg_file = os.path.join(path, 'package.json')
                if os.path.exists(pkg_file):
                    with open(pkg_file, 'rb') as f:
                        pkg_hash = hashlib.md5(f.read()).hexdigest()[:12]
                    lock_hash = ''
                    for lock_name in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']:
                        lock_file = os.path.join(path, lock_name)
                        if os.path.exists(lock_file):
                            with open(lock_file, 'rb') as f:
                                lock_hash = hashlib.md5(f.read()).hexdigest()[:8]
                            break
                    repo_key = f"fe-{pkg_hash}-{lock_hash}" if lock_hash else f"fe-{pkg_hash}"
                    node_cache = os.path.join(self.cache_root, repo_key, 'node_modules')
                    if os.path.exists(node_cache):
                        log("   [Auto-fix] removing cached node_modules")
                        subprocess.run(f'rd /s /q "{node_cache}"', shell=True, capture_output=True, timeout=120)
            except Exception as e:
                log(f"   [WARN] Cache removal failed: {str(e)[:100]}")

            log("   Retrying build...")
            result = self._build_frontend(repo_dir, subdir, log)

            if result.get('success'):
                log(f"   [OK] Auto-fix succeeded on retry {retry}!")
                return result

            log(f"   [FAIL] Retry {retry} failed")

        log("   [WARN] All auto-fix retries failed")
        return result

    # ============================================
    # DETECT FRONTEND FRAMEWORK
    # ============================================
    def _detect_frontend_framework(self, path):
        pkg_file = os.path.join(path, 'package.json')
        if not os.path.exists(pkg_file):
            return 'static'

        try:
            with open(pkg_file, encoding='utf-8') as f:
                pkg = json.load(f)
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            scripts = pkg.get('scripts', {})

            if 'next' in deps:
                return 'next'
            if 'nuxt' in deps or 'nuxt3' in deps:
                return 'nuxt'
            if '@angular/core' in deps:
                return 'angular'
            if '@sveltejs/kit' in deps:
                return 'sveltekit'
            if 'vite' in deps:
                if 'vue' in deps:
                    return 'vite-vue'
                if 'svelte' in deps:
                    return 'vite-svelte'
                if 'react' in deps:
                    return 'vite-react'
                return 'vite'
            if 'react-scripts' in deps:
                return 'cra'
            if '@vue/cli-service' in deps:
                return 'vue-cli'
            if 'react' in deps:
                return 'react'
            if 'vue' in deps:
                return 'vue'
            if 'svelte' in deps:
                return 'svelte'
            if 'build' in scripts:
                return 'node-build'
            return 'node'
        except Exception:
            return 'static'

    # ============================================
    # BUILD FRONTEND (Universal)
    # ============================================
    def _build_frontend(self, repo_dir, subdir, log):
        try:
            path = repo_dir if subdir == '.' else os.path.join(repo_dir, subdir)

            if not os.path.exists(os.path.join(path, 'package.json')):
                # ⭐ NEW: ANY .html file → auto-rename to index.html
                if self._ensure_index_html(path, log):
                    log("   Static HTML (no build needed)")
                    return {
                        'success': True,
                        'build_path': path,
                        'framework': 'static',
                        'serve_mode': 'static',
                    }
                return {'success': False, 'error': 'No package.json or HTML file'}

            framework = self._detect_frontend_framework(path)
            log(f"   Framework detected: {framework}")

            if os.path.exists(os.path.join(path, 'pnpm-lock.yaml')):
                install_cmd = 'pnpm install --prefer-offline'
                build_cmd = 'pnpm run build'
            elif os.path.exists(os.path.join(path, 'yarn.lock')):
                install_cmd = 'yarn install --prefer-offline'
                build_cmd = 'yarn build'
            else:
                install_cmd = 'npm install --no-audit --no-fund --legacy-peer-deps'
                build_cmd = 'npm run build'

            pkg_file = os.path.join(path, 'package.json')
            try:
                with open(pkg_file, 'rb') as f:
                    pkg_hash = hashlib.md5(f.read()).hexdigest()[:12]
            except Exception:
                pkg_hash = 'unknown'

            lock_hash = ''
            for lock_name in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']:
                lock_file = os.path.join(path, lock_name)
                if os.path.exists(lock_file):
                    try:
                        with open(lock_file, 'rb') as f:
                            lock_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    except Exception:
                        pass
                    break

            repo_key = f"fe-{pkg_hash}-{lock_hash}" if lock_hash else f"fe-{pkg_hash}"
            node_cache = os.path.join(self.cache_root, repo_key, 'node_modules')
            log(f"   Cache key: {repo_key}")

            use_cache = False
            if self.ENABLE_NODE_CACHE and os.path.exists(node_cache) and os.path.exists(os.path.join(node_cache, '.complete')):
                log("   Cache found - restoring")
                dest = os.path.join(path, 'node_modules')
                if os.path.exists(dest):
                    try:
                        subprocess.run(f'rd /s /q "{dest}"', shell=True, capture_output=True, timeout=60)
                    except Exception:
                        shutil.rmtree(dest, ignore_errors=True)

                if self.USE_JUNCTION and os.name == 'nt':
                    try:
                        result = subprocess.run(
                            f'mklink /J "{dest}" "{node_cache}"',
                            shell=True, capture_output=True, text=True, timeout=30
                        )
                        if 'Junction created' in result.stdout or result.returncode == 0:
                            log("   node_modules linked (junction - 0s)")
                            use_cache = True
                    except Exception:
                        pass

                if not use_cache:
                    try:
                        shutil.copytree(node_cache, dest, copy_function=os.link)
                        use_cache = True
                    except Exception:
                        try:
                            shutil.copytree(node_cache, dest)
                            use_cache = True
                        except Exception:
                            pass

            if not use_cache:
                log("   Fresh install")
                start = time.time()
                success, output = self._run_streaming(install_cmd, path, log, self.TIMEOUT_INSTALL)
                elapsed = time.time() - start
                log(f"   Install took {elapsed:.1f}s")

                if not success:
                    return {'success': False, 'error': 'Install failed', 'output': output}

                if self.ENABLE_NODE_CACHE:
                    try:
                        os.makedirs(os.path.dirname(node_cache), exist_ok=True)
                        if os.path.exists(node_cache):
                            subprocess.run(f'rd /s /q "{node_cache}"', shell=True, capture_output=True, timeout=120)
                        nm = os.path.join(path, 'node_modules')
                        if os.path.exists(nm):
                            log("   Saving cache (MOVE)...")
                            try:
                                shutil.move(nm, node_cache)
                                if self.USE_JUNCTION and os.name == 'nt':
                                    subprocess.run(
                                        f'mklink /J "{nm}" "{node_cache}"',
                                        shell=True, capture_output=True, timeout=30
                                    )
                                with open(os.path.join(node_cache, '.complete'), 'w') as f:
                                    f.write('ok')
                            except Exception:
                                shutil.copytree(nm, node_cache)
                                with open(os.path.join(node_cache, '.complete'), 'w') as f:
                                    f.write('ok')
                    except Exception as e:
                        log(f"   [WARN] Cache save: {str(e)[:80]}")
            else:
                log("   Skipping npm install")

            log("   Building...")
            build_env = os.environ.copy()
            build_env['NODE_OPTIONS'] = '--max-old-space-size=4096'
            build_env['GENERATE_SOURCEMAP'] = 'false'
            build_env['CI'] = 'false'
            build_env['DISABLE_ESLINT_PLUGIN'] = 'true'
            build_env['TSC_COMPILE_ON_ERROR'] = 'true'
            build_env['FAST_REFRESH'] = 'false'
            build_env['SKIP_PREFLIGHT_CHECK'] = 'true'

            start = time.time()
            success, output = self._run_streaming(build_cmd, path, log, self.TIMEOUT_BUILD, env=build_env)
            elapsed = time.time() - start
            log(f"   Build took {elapsed:.1f}s")

            if not success:
                return {'success': False, 'error': 'Build failed', 'output': output}

            build_path, serve_mode = self._resolve_build_output(path, framework, log)

            if not build_path:
                build_path = path
                serve_mode = 'static'

            return {
                'success': True,
                'build_path': build_path,
                'framework': framework,
                'serve_mode': serve_mode,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)[:200], 'output': str(e)}

    # ============================================
    # RESOLVE BUILD OUTPUT
    # ============================================
    def _resolve_build_output(self, path, framework, log):
        if framework == 'next':
            if os.path.exists(os.path.join(path, '.next')):
                log("   Built to .next/ (Next.js server mode)")
                return (path, 'server')
            return (path, 'server')

        if framework == 'nuxt':
            if os.path.exists(os.path.join(path, '.output')):
                log("   Built to .output/ (Nuxt server mode)")
                return (path, 'server')
            return (path, 'server')

        if framework == 'sveltekit':
            if os.path.exists(os.path.join(path, 'build')):
                log("   Built to build/ (SvelteKit server mode)")
                return (os.path.join(path, 'build'), 'server')
            return (path, 'server')

        if framework == 'angular':
            for sub in ['dist', os.path.join('dist', 'browser')]:
                candidate = os.path.join(path, sub)
                if os.path.exists(candidate):
                    log(f"   Built to {sub}/ (static)")
                    return (candidate, 'spa')
            return (path, 'spa')

        for sub in ['dist', 'build', 'out', 'public', 'www']:
            candidate = os.path.join(path, sub)
            if os.path.exists(candidate):
                if os.path.exists(os.path.join(candidate, 'index.html')):
                    log(f"   Built to {sub}/ (SPA)")
                    return (candidate, 'spa')
                log(f"   Built to {sub}/ (static)")
                return (candidate, 'static')

        if os.path.exists(os.path.join(path, 'index.html')):
            log("   Built to ./ (static)")
            return (path, 'static')

        return (path, 'static')

    # ============================================
    # START FRONTEND SERVER (Next.js, Nuxt, etc.)
    # ============================================
    def _start_frontend_server(self, deploy_id, deploy_dir, repo_dir, subdir, framework, port, log):
        try:
            path = repo_dir if subdir == '.' else os.path.join(repo_dir, subdir)
            log_file = os.path.join(deploy_dir, 'frontend.log')

            if framework == 'next':
                cmd = f'npx next start -p {port}'
            elif framework == 'nuxt':
                if os.name == 'nt':
                    cmd = f'set PORT={port} && node .output/server/index.mjs'
                else:
                    cmd = f'PORT={port} node .output/server/index.mjs'
            elif framework == 'sveltekit':
                if os.name == 'nt':
                    cmd = f'set PORT={port} && node build'
                else:
                    cmd = f'PORT={port} node build'
            else:
                cmd = 'npm start'

            log(f"   Start: {cmd}")

            env = os.environ.copy()
            env['PORT'] = str(port)

            if os.name == 'nt':
                proc = subprocess.Popen(
                    cmd, cwd=path, shell=True,
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    env=env, creationflags=DETACHED_FLAGS, close_fds=True,
                )
            else:
                proc = subprocess.Popen(
                    cmd, cwd=path, shell=True,
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    env=env, start_new_session=True, close_fds=True,
                )

            log(f"   Frontend server started (PID: {proc.pid}, port {port})")

            for i in range(15):
                time.sleep(1)
                if self._port_listening(port):
                    log(f"   [OK] Frontend server listening on port {port}")
                    break
            else:
                log(f"   [WARN] Frontend server not listening on {port} yet")

            return proc
        except Exception as e:
            log(f"   [WARN] Frontend server failed: {str(e)[:150]}")
            return None

    # ============================================
    # BUILD BACKEND
    # ============================================
    def _build_backend(self, repo_dir, subdir, lang, log):
        try:
            path = repo_dir if subdir == '.' else os.path.join(repo_dir, subdir)

            if lang == 'python':
                log("   Python deps...")
                req_file = os.path.join(path, 'requirements.txt')
                if not os.path.exists(req_file):
                    return {'success': True, 'runtime': 'python', 'path': path}

                venv_path = os.path.join(path, '.venv')
                try:
                    with open(req_file, 'rb') as f:
                        req_hash = hashlib.md5(f.read()).hexdigest()[:12]
                except Exception:
                    req_hash = 'unknown'

                repo_key = f"be-{req_hash}"
                venv_cache = os.path.join(self.cache_root, repo_key, 'venv')
                log(f"   Cache key: {repo_key}")

                used_cache = False
                if self.ENABLE_VENV_CACHE and os.path.exists(venv_cache) and os.path.exists(os.path.join(venv_cache, '.complete')):
                    log("   venv cache found")
                    if os.path.exists(venv_path):
                        try:
                            subprocess.run(f'rd /s /q "{venv_path}"', shell=True, capture_output=True, timeout=60)
                        except Exception:
                            shutil.rmtree(venv_path, ignore_errors=True)

                    if self.USE_JUNCTION and os.name == 'nt':
                        try:
                            result = subprocess.run(
                                f'mklink /J "{venv_path}" "{venv_cache}"',
                                shell=True, capture_output=True, text=True, timeout=30
                            )
                            if 'Junction created' in result.stdout or result.returncode == 0:
                                log("   venv linked (0s)")
                                used_cache = True
                        except Exception:
                            pass

                    if not used_cache:
                        try:
                            shutil.copytree(venv_cache, venv_path, copy_function=os.link)
                            used_cache = True
                        except Exception:
                            try:
                                shutil.copytree(venv_cache, venv_path)
                                used_cache = True
                            except Exception:
                                pass

                if not used_cache:
                    if not os.path.exists(venv_path):
                        log("   Creating venv...")
                        self._run_streaming('python -m venv .venv', path, log, self.TIMEOUT_VENV)

                    if os.name == 'nt':
                        pip = os.path.join(venv_path, 'Scripts', 'pip.exe')
                    else:
                        pip = os.path.join(venv_path, 'bin', 'pip')
                    if not os.path.exists(pip):
                        pip = 'pip'

                    log("   pip install...")
                    pip_cmd = f'"{pip}" install -r requirements.txt --prefer-binary --disable-pip-version-check'
                    self._run_streaming(pip_cmd, path, log, self.TIMEOUT_PIP)

                    if self.ENABLE_VENV_CACHE:
                        try:
                            os.makedirs(os.path.dirname(venv_cache), exist_ok=True)
                            if os.path.exists(venv_cache):
                                subprocess.run(f'rd /s /q "{venv_cache}"', shell=True, capture_output=True, timeout=120)
                            try:
                                shutil.move(venv_path, venv_cache)
                                if self.USE_JUNCTION and os.name == 'nt':
                                    subprocess.run(
                                        f'mklink /J "{venv_path}" "{venv_cache}"',
                                        shell=True, capture_output=True, timeout=30
                                    )
                                with open(os.path.join(venv_cache, '.complete'), 'w') as f:
                                    f.write('ok')
                            except Exception:
                                shutil.copytree(venv_path, venv_cache)
                                with open(os.path.join(venv_cache, '.complete'), 'w') as f:
                                    f.write('ok')
                        except Exception as e:
                            log(f"   [WARN] Cache save: {str(e)[:80]}")
                else:
                    log("   Skipping venv + pip")

                return {'success': True, 'runtime': 'python', 'path': path}

            if lang == 'node':
                install_cmd = 'npm install --no-audit --no-fund --legacy-peer-deps'
                self._run_streaming(install_cmd, path, log, self.TIMEOUT_INSTALL)
                return {'success': True, 'runtime': 'node', 'path': path}

            if lang == 'go':
                self._run_streaming('go mod download', path, log, 900)
                self._run_streaming('go build -o app .', path, log, 900)
                return {'success': True, 'runtime': 'go', 'path': path}

            if lang == 'rust':
                self._run_streaming('cargo build --release', path, log, 1800)
                return {'success': True, 'runtime': 'rust', 'path': path}

            if lang == 'php':
                self._run_streaming('composer install --no-dev --prefer-dist', path, log, 900)
                return {'success': True, 'runtime': 'php', 'path': path}

            if lang == 'java':
                self._run_streaming('mvn package -DskipTests', path, log, 1800)
                return {'success': True, 'runtime': 'java', 'path': path}

            if lang == 'ruby':
                self._run_streaming('bundle install --jobs 4', path, log, 900)
                return {'success': True, 'runtime': 'ruby', 'path': path}

            return {'success': False, 'error': f'Unsupported: {lang}'}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    # ============================================
    # DETECT STRUCTURE
    # ============================================
    def _detect_structure(self, repo_dir):
        detection = {
            'type': 'unknown', 'languages': [],
            'frontend': None, 'frontend_framework': None,
            'backend': None, 'backend_lang': None,
        }

        # ⭐ NEW: FIRST check for ANY .html file at root (no package.json)
        try:
            root_files = os.listdir(repo_dir)
            html_files_at_root = [
                f for f in root_files
                if f.lower().endswith('.html')
                and os.path.isfile(os.path.join(repo_dir, f))
            ]
            has_pkg_at_root = os.path.exists(os.path.join(repo_dir, 'package.json'))

            if html_files_at_root and not has_pkg_at_root:
                detection['frontend'] = '.'
                detection['frontend_framework'] = 'static'
                detection['type'] = 'frontend'
                detection['languages'].append('static')
                print(f"[SELF-HOST] Found HTML entry: {html_files_at_root[0]} (will rename to index.html)")
                return detection
        except Exception as e:
            print(f"[SELF-HOST] HTML detection error: {e}")

        for candidate in ['.', 'frontend', 'client', 'web', 'app', 'ui']:
            base = repo_dir if candidate == '.' else os.path.join(repo_dir, candidate)
            if not os.path.isdir(base):
                continue
            pkg_path = os.path.join(base, 'package.json')
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, encoding='utf-8') as f:
                        pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    if any(fw in deps for fw in ['react', 'vue', 'next', 'svelte', 'angular', 'vite', 'nuxt', '@sveltejs/kit']):
                        detection['frontend'] = candidate
                        detection['frontend_framework'] = self._detect_frontend_framework(base)
                        if 'node' not in detection['languages']:
                            detection['languages'].append('node')
                        break
                except Exception:
                    pass
            if candidate == '.' and os.path.exists(os.path.join(base, 'index.html')):
                if not detection['frontend']:
                    detection['frontend'] = '.'
                    detection['frontend_framework'] = 'static'
                    if 'static' not in detection['languages']:
                        detection['languages'].append('static')

        for candidate in ['backend', 'server', 'api', '.', 'src']:
            base = repo_dir if candidate == '.' else os.path.join(repo_dir, candidate)
            if not os.path.isdir(base):
                continue
            if candidate == detection.get('frontend'):
                continue

            for lang, files in self.LANG_PATTERNS.items():
                if lang in ('node', 'static'):
                    continue
                for marker in files:
                    if os.path.exists(os.path.join(base, marker)):
                        detection['backend'] = candidate
                        detection['backend_lang'] = lang
                        if lang not in detection['languages']:
                            detection['languages'].append(lang)
                        break
                if detection['backend']:
                    break
            if detection['backend']:
                break

            pkg_path = os.path.join(base, 'package.json')
            if os.path.exists(pkg_path):
                try:
                    with open(pkg_path, encoding='utf-8') as f:
                        pkg = json.load(f)
                    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    if any(fw in deps for fw in ['express', 'koa', 'fastify', 'nest', '@nestjs/core']):
                        detection['backend'] = candidate
                        detection['backend_lang'] = 'node'
                        if 'node' not in detection['languages']:
                            detection['languages'].append('node')
                        break
                except Exception:
                    pass

        if detection['frontend'] and detection['backend']:
            detection['type'] = 'fullstack'
        elif detection['frontend']:
            detection['type'] = 'frontend'
        elif detection['backend']:
            detection['type'] = 'backend'
        elif os.path.exists(os.path.join(repo_dir, 'package.json')):
            detection['frontend'] = '.'
            detection['frontend_framework'] = self._detect_frontend_framework(repo_dir)
            detection['type'] = 'frontend'
            detection['languages'].append('node')

        return detection

    # ============================================
    # START BACKEND
    # ============================================
    def _start_backend(self, deploy_id, deploy_dir, repo_dir, subdir, lang, port, log):
        try:
            path = repo_dir if subdir == '.' else os.path.join(repo_dir, subdir)
            log_file = os.path.join(deploy_dir, 'backend.log')

            cmd = self._detect_start_cmd(path, lang, port)
            log(f"   Start: {cmd}")

            env = os.environ.copy()
            env['PORT'] = str(port)

            if os.name == 'nt':
                proc = subprocess.Popen(
                    cmd, cwd=path, shell=True,
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    env=env, creationflags=DETACHED_FLAGS, close_fds=True,
                )
            else:
                proc = subprocess.Popen(
                    cmd, cwd=path, shell=True,
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    env=env, start_new_session=True, close_fds=True,
                )

            log(f"   Backend started (PID: {proc.pid}, detached)")
            time.sleep(2)
            return proc
        except Exception as e:
            log(f"   [WARN] Backend failed: {str(e)[:150]}")
            return None

    def _detect_start_cmd(self, path, lang, port):
        if lang == 'python':
            if os.path.exists(os.path.join(path, 'manage.py')):
                return f'python manage.py runserver 0.0.0.0:{port}'
            if os.path.exists(os.path.join(path, 'main.py')):
                try:
                    with open(os.path.join(path, 'main.py'), encoding='utf-8') as f:
                        content = f.read()
                    if 'FastAPI' in content:
                        return f'uvicorn main:app --host 0.0.0.0 --port {port}'
                except Exception:
                    pass
                return 'python main.py'
            if os.path.exists(os.path.join(path, 'app.py')):
                return 'python app.py'
            if os.path.exists(os.path.join(path, 'run.py')):
                return 'python run.py'
            return 'python app.py'
        if lang == 'node':
            pkg_file = os.path.join(path, 'package.json')
            if os.path.exists(pkg_file):
                try:
                    with open(pkg_file, encoding='utf-8') as f:
                        pkg = json.load(f)
                    scripts = pkg.get('scripts', {})
                    if 'start' in scripts:
                        return 'npm start'
                except Exception:
                    pass
            for entry in ['server.js', 'index.js', 'app.js', 'main.js']:
                if os.path.exists(os.path.join(path, entry)):
                    return f'node {entry}'
            return 'npm start'
        if lang == 'go':
            return './app'
        if lang == 'rust':
            return 'cargo run --release'
        if lang == 'php':
            return f'php -S 0.0.0.0:{port}'
        return 'echo "no start command"'

    # ============================================
    # START PROXY - RELIABLE BACKGROUND PROCESS
    # ============================================
    def _start_proxy(self, deploy_id, deploy_dir,
                     frontend_ready, frontend_path, frontend_serve_mode,
                     backend_ready, backend_port, proxy_port,
                     frontend_server_port=None, log=None):
        if log is None:
            log = lambda msg, level='info': print(f"[SELF-HOST] {msg}")

        try:
            proxy_script = os.path.join(deploy_dir, 'proxy.py')
            frontend_path_safe = (frontend_path or '').replace('\\', '/')
            serve_mode = frontend_serve_mode or 'static'

            if serve_mode == 'server' and frontend_server_port:
                target_port = frontend_server_port
                log(f"   [Proxy] Server mode: routing to port {target_port}")
            elif backend_ready:
                target_port = backend_port
                log(f"   [Proxy] Fullstack mode: routing /api to port {target_port}")
            else:
                target_port = 0
                log(f"   [Proxy] Static mode: no backend")

            script = f'''"""Universal proxy - handles static, SPA, and server modes."""
import http.server
import socketserver
import urllib.request
import urllib.parse
import os
import posixpath
import sys


PROXY_PORT = {proxy_port}
FRONTEND_PATH = r"{frontend_path_safe}"
TARGET_PORT = {target_port}
FRONTEND_READY = {frontend_ready}
SERVE_MODE = "{serve_mode}"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _proxy_to_target(self, path_override=None):
        try:
            path = path_override if path_override is not None else self.path
            url = f'http://127.0.0.1:{{TARGET_PORT}}{{path}}'
            body = None
            if self.command in ('POST', 'PUT', 'PATCH', 'DELETE'):
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else None
            req = urllib.request.Request(url, data=body, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ('host', 'content-length'):
                    req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ('transfer-encoding', 'connection'):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            try:
                self.send_error(502, str(e)[:200])
            except Exception:
                pass

    def _serve_static(self):
        if not FRONTEND_PATH or not os.path.exists(FRONTEND_PATH):
            self.send_error(404, 'Frontend not built')
            return
        path = self.translate_path(self.path)
        if not os.path.exists(path) or os.path.isdir(path):
            index = os.path.join(FRONTEND_PATH, 'index.html')
            if os.path.exists(index):
                self.path = '/index.html'
                path = index
            else:
                self.send_error(404)
                return
        return super().do_GET()

    def do_GET(self):
        if self.path == '/_health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        if SERVE_MODE == 'server' and FRONTEND_READY and TARGET_PORT:
            return self._proxy_to_target()

        if self.path.startswith('/api/') and TARGET_PORT:
            return self._proxy_to_target(path_override=self.path[4:])

        return self._serve_static()

    def do_POST(self):
        if SERVE_MODE == 'server' and FRONTEND_READY and TARGET_PORT:
            return self._proxy_to_target()
        if self.path.startswith('/api/') and TARGET_PORT:
            return self._proxy_to_target(path_override=self.path[4:])
        self.send_error(404)

    def do_PUT(self):
        if SERVE_MODE == 'server' and FRONTEND_READY and TARGET_PORT:
            return self._proxy_to_target()
        if self.path.startswith('/api/') and TARGET_PORT:
            return self._proxy_to_target(path_override=self.path[4:])
        self.send_error(404)

    def do_DELETE(self):
        if SERVE_MODE == 'server' and FRONTEND_READY and TARGET_PORT:
            return self._proxy_to_target()
        if self.path.startswith('/api/') and TARGET_PORT:
            return self._proxy_to_target(path_override=self.path[4:])
        self.send_error(404)

    def translate_path(self, path):
        if not FRONTEND_PATH:
            return ''
        path = path.split('?', 1)[0].split('#', 1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = [w for w in path.split('/') if w]
        result = FRONTEND_PATH
        for word in words:
            if word in (os.curdir, os.pardir):
                continue
            result = os.path.join(result, word)
        return result


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    print(f'[PROXY] Starting on port {{PROXY_PORT}} (mode={{SERVE_MODE}}, target={{TARGET_PORT}})', flush=True)
    try:
        with ThreadingTCPServer(('0.0.0.0', PROXY_PORT), ProxyHandler) as httpd:
            print(f'[PROXY] Listening on {{PROXY_PORT}}', flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f'[PROXY] FATAL: {{e}}', flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
'''
            with open(proxy_script, 'w', encoding='utf-8') as f:
                f.write(script)

            log_file = os.path.join(deploy_dir, 'proxy.log')

            if os.name == 'nt':
                proc = subprocess.Popen(
                    [sys.executable, proxy_script],
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    creationflags=PROXY_FLAGS,
                    close_fds=True,
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, proxy_script],
                    stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    close_fds=True,
                )
            log(f"   Proxy started (port {proxy_port}, mode={serve_mode}, PID: {proc.pid})")

            for i in range(10):
                time.sleep(0.5)
                if self._port_listening(proxy_port):
                    log(f"   [OK] Proxy is listening on port {proxy_port}")
                    return proc

            log(f"   [WARN] Proxy not listening on {proxy_port} after 5s")
            try:
                with open(log_file, encoding='utf-8', errors='replace') as f:
                    content = f.read()
                if content:
                    log(f"   [Proxy log] {content[:500]}")
            except Exception:
                pass
            return proc

        except Exception as e:
            log(f"   [WARN] Proxy failed: {str(e)[:150]}")
            import traceback
            traceback.print_exc()
            return None

    # ============================================
    # EXPOSE URL - Cloudflare
    # ============================================
    def _expose_url(self, deploy_id, proxy_port, log, owner=None, repo=None):
        slug = self._slug_from_repo(owner or '', repo or '') or deploy_id[:20]
        subdomain = f"{slug}.{self.base_domain}"

        try:
            if self.cf_token and self.cf_zone:
                log(f"   Cloudflare: {subdomain}")

                dns_url = f"https://api.cloudflare.com/client/v4/zones/{self.cf_zone}/dns_records"
                dns_payload = json.dumps({
                    "type": "CNAME",
                    "name": subdomain,
                    "content": f"{self.cf_tunnel_id}.cfargotunnel.com",
                    "proxied": True
                }).encode()

                req = urllib.request.Request(
                    dns_url,
                    data=dns_payload,
                    headers={
                        "Authorization": f"Bearer {self.cf_token}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )

                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        result = json.loads(resp.read().decode())
                        if result.get('success'):
                            log("   DNS record created")
                        else:
                            errors = result.get('errors', [])
                            err_str = str(errors).lower()
                            if 'already exists' in err_str or 'duplicate' in err_str:
                                log("   DNS record already exists")
                            else:
                                log(f"   DNS error: {errors}")
                except urllib.error.HTTPError as http_err:
                    body = http_err.read().decode(errors='replace')
                    if 'already exists' in body.lower() or 'duplicate' in body.lower():
                        log("   DNS record already exists")
                    else:
                        log(f"   DNS request failed: {str(http_err)[:120]}")
                except Exception as dns_err:
                    log(f"   DNS request failed: {str(dns_err)[:120]}")

                try:
                    self._update_tunnel_config(subdomain, proxy_port, log)
                except Exception as cfg_err:
                    log(f"   Tunnel config update failed: {str(cfg_err)[:120]}")

                try:
                    self._restart_cloudflared(log)
                except Exception as cf_err:
                    log(f"   Cloudflared restart failed: {str(cf_err)[:120]}")

                public_url = f"https://{subdomain}"
                log(f"   Cloudflare URL: {public_url}")

                try:
                    info_file = os.path.join(self.deploy_root, deploy_id, 'tunnel.json')
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'url': public_url,
                            'type': 'cloudflare',
                            'subdomain': subdomain,
                            'proxy_port': proxy_port,
                            'tunnel_id': self.cf_tunnel_id,
                            'created_at': time.time(),
                        }, f, indent=2)
                except Exception:
                    pass

                return public_url
            else:
                log("   CLOUDFLARE_API_TOKEN or CLOUDFLARE_ZONE_ID missing")

        except Exception as e:
            log(f"   Cloudflare failed: {str(e)[:150]}")

        local_url = f'http://localhost:{proxy_port}'
        log(f"   Local only: {local_url}")
        return local_url

    # ============================================
    # UPDATE TUNNEL CONFIG
    # ============================================
    def _update_tunnel_config(self, subdomain, port, log):
        try:
            import yaml
        except ImportError:
            log("   pyyaml not installed")
            return

        config_path = Path.home() / ".cloudflared" / "config.yml"
        if not config_path.exists():
            log("   config.yml not found")
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        if "ingress" not in config:
            config["ingress"] = []

        existing = [r for r in config["ingress"] if r.get("hostname") == subdomain]
        if existing:
            existing[0]["service"] = f"http://localhost:{port}"
            log("   Updated existing ingress rule")
        else:
            new_rule = {"hostname": subdomain, "service": f"http://localhost:{port}"}
            catch_all = [r for r in config["ingress"] if r.get("service") == "http_status:404"]
            config["ingress"] = [r for r in config["ingress"] if r.get("service") != "http_status:404"]
            config["ingress"].append(new_rule)
            if catch_all:
                config["ingress"].append(catch_all[0])
            else:
                config["ingress"].append({"service": "http_status:404"})
            log("   Added new ingress rule")

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)

        log("   config.yml updated")

    # ============================================
    # RESTART CLOUDFLARED WITH VERIFICATION
    # ============================================
    def _restart_cloudflared(self, log):
        try:
            subprocess.run('taskkill /F /IM cloudflared.exe', shell=True, capture_output=True, timeout=10)
            log("   [Cloudflared] Killed old process")
            time.sleep(2)

            if os.name == 'nt':
                subprocess.Popen(
                    f'cloudflared tunnel run {self.cf_tunnel_name}',
                    shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=DETACHED_FLAGS, close_fds=True,
                )
            else:
                subprocess.Popen(
                    f'cloudflared tunnel run {self.cf_tunnel_name}',
                    shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True, close_fds=True,
                )

            for i in range(15):
                time.sleep(1)
                result = subprocess.run(
                    'tasklist /FI "IMAGENAME eq cloudflared.exe" /NH',
                    shell=True, capture_output=True, text=True, timeout=5,
                )
                if 'cloudflared.exe' in result.stdout:
                    log(f"   [Cloudflared] Running (verified after {i+1}s)")
                    time.sleep(3)
                    return True

            log("   [Cloudflared] WARNING: not running after 15s")
            return False

        except Exception as e:
            log(f"   [WARN] Restart error: {str(e)[:100]}")
            return False

    # ============================================
    # RESTORE ALL
    # ============================================
    def restore_all(self, log=None):
        if log is None:
            log = lambda msg, level='info': print(f"[RESTORE] {msg}")

        registry = self.list_deployments()
        restored = {'proxy': [], 'backend': [], 'frontend': [], 'tunnel': []}

        for deploy_id, data in registry.items():
            if data.get('status') != 'success':
                continue

            deploy_dir = os.path.join(self.deploy_root, deploy_id)
            if not os.path.isdir(deploy_dir):
                continue

            proxy_port = data.get('proxy_port')
            backend_port = data.get('backend_port')
            backend_ready = bool(data.get('backend_ready', False))
            frontend_ready = bool(data.get('frontend_ready', False))
            serve_mode = data.get('frontend_serve_mode', 'static')
            frontend_server_port = data.get('frontend_server_port')

            if frontend_ready and serve_mode == 'server' and frontend_server_port:
                log(f"Frontend server check for {deploy_id}")
                repo_dir = os.path.join(deploy_dir, 'repo')
                if os.path.isdir(repo_dir) and not self._port_listening(frontend_server_port):
                    try:
                        detection = self._detect_structure(repo_dir)
                        fe_proc = self._start_frontend_server(
                            deploy_id, deploy_dir, repo_dir,
                            detection['frontend'],
                            detection.get('frontend_framework', 'next'),
                            frontend_server_port, log,
                        )
                        if fe_proc:
                            self.active_processes.setdefault(deploy_id, {})['frontend'] = fe_proc
                            restored['frontend'].append(deploy_id)
                    except Exception as e:
                        log(f"   Frontend restart failed: {e}")

            if backend_ready and backend_port and not self._port_listening(backend_port):
                log(f"Backend down for {deploy_id}")
                repo_dir = os.path.join(deploy_dir, 'repo')
                if os.path.isdir(repo_dir):
                    try:
                        detection = self._detect_structure(repo_dir)
                        if detection.get('backend'):
                            be_proc = self._start_backend(
                                deploy_id, deploy_dir, repo_dir,
                                detection['backend'],
                                detection.get('backend_lang', 'unknown'),
                                backend_port, log,
                            )
                            if be_proc:
                                self.active_processes.setdefault(deploy_id, {})['backend'] = be_proc
                                restored['backend'].append(deploy_id)
                    except Exception as e:
                        log(f"   Backend restart failed: {e}")

            if proxy_port and not self._port_listening(proxy_port):
                log(f"Proxy down for {deploy_id}")
                proxy_script = os.path.join(deploy_dir, 'proxy.py')
                if os.path.exists(proxy_script):
                    try:
                        log_file = os.path.join(deploy_dir, 'proxy-restore.log')
                        if os.name == 'nt':
                            proc = subprocess.Popen(
                                [sys.executable, proxy_script],
                                stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                                stderr=subprocess.STDOUT,
                                creationflags=PROXY_FLAGS,
                                close_fds=True,
                            )
                        else:
                            proc = subprocess.Popen(
                                [sys.executable, proxy_script],
                                stdout=open(log_file, 'w', encoding='utf-8', errors='replace'),
                                stderr=subprocess.STDOUT,
                                start_new_session=True, close_fds=True,
                            )
                        self.active_processes.setdefault(deploy_id, {})['proxy'] = proc
                        restored['proxy'].append(deploy_id)
                        log(f"   Proxy restarted (PID: {proc.pid})")
                    except Exception as e:
                        log(f"   Proxy restart failed: {e}")

            info_file = os.path.join(deploy_dir, 'tunnel.json')
            if os.path.exists(info_file) and proxy_port:
                try:
                    with open(info_file, encoding='utf-8') as f:
                        info = json.load(f)

                    if info.get('type') == 'cloudflare':
                        result = subprocess.run(
                            'tasklist /FI "IMAGENAME eq cloudflared.exe" /NH',
                            shell=True, capture_output=True, text=True, timeout=5,
                        )
                        if 'cloudflared.exe' in result.stdout:
                            self._tunnel_procs[deploy_id] = {'url': info.get('url'), 'restored': True}
                        else:
                            log(f"Cloudflare tunnel down for {deploy_id}")
                            try:
                                self._restart_cloudflared(log)
                                restored['tunnel'].append(deploy_id)
                            except Exception as e:
                                log(f"   Tunnel restart failed: {e}")
                except Exception as e:
                    log(f"   Tunnel check failed: {e}")

        log(f"Restored: {len(restored['frontend'])} frontend, {len(restored['backend'])} backend, "
            f"{len(restored['proxy'])} proxy, {len(restored['tunnel'])} tunnel")
        return restored

    # ============================================
    # REGISTRY
    # ============================================
    def list_deployments(self):
        registry = {}
        with _REGISTRY_LOCK:
            if os.path.exists(self.registry_file):
                try:
                    with open(self.registry_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            registry = json.loads(content)
                except json.JSONDecodeError:
                    registry = {}
                    try:
                        shutil.copy(self.registry_file, self.registry_file + '.corrupt')
                        self._write_registry(registry)
                    except Exception:
                        pass
                except Exception:
                    registry = {}
        return registry

    def get_deployment(self, deploy_id):
        return self.list_deployments().get(deploy_id)

    def stop_deployment(self, deploy_id):
        try:
            procs = self.active_processes.get(deploy_id, {})
            killed = []
            for proc_type, proc in procs.items():
                if proc and hasattr(proc, 'poll') and proc.poll() is None:
                    try:
                        proc.terminate()
                        killed.append(proc_type)
                    except Exception:
                        pass

            tunnel = self._tunnel_procs.get(deploy_id)
            if tunnel and isinstance(tunnel, dict):
                pid = tunnel.get('pid')
                if pid:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True, timeout=5)
                    killed.append('tunnel')

            self.active_processes.pop(deploy_id, None)
            self._tunnel_procs.pop(deploy_id, None)

            registry = self.list_deployments()
            if deploy_id in registry:
                registry[deploy_id]['status'] = 'stopped'
                registry[deploy_id]['stopped_at'] = time.time()
                self._write_registry(registry)

            return {'success': True, 'deploy_id': deploy_id, 'killed': killed}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    def delete_deployment(self, deploy_id):
        try:
            self.stop_deployment(deploy_id)
            registry = self.list_deployments()
            if deploy_id in registry:
                del registry[deploy_id]
                self._write_registry(registry)

            deploy_dir = os.path.join(self.deploy_root, deploy_id)
            if os.path.exists(deploy_dir):
                try:
                    subprocess.run(f'rd /s /q "{deploy_dir}"', shell=True, capture_output=True, timeout=300)
                except Exception:
                    shutil.rmtree(deploy_dir, ignore_errors=True)

            return {'success': True, 'deploy_id': deploy_id}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    def _update_registry_status(self, deploy_id, status, error=None):
        registry = self.list_deployments()
        if deploy_id in registry:
            registry[deploy_id]['status'] = status
            if error:
                registry[deploy_id]['error'] = error
            registry[deploy_id]['updated_at'] = time.time()
            self._write_registry(registry)

    def _save_to_registry(self, deploy_id, data):
        registry = self.list_deployments()
        registry[deploy_id] = data
        self._write_registry(registry)

    def _write_registry(self, registry):
        with _REGISTRY_LOCK:
            try:
                with open(self.registry_file, 'w', encoding='utf-8') as f:
                    json.dump(registry, f, indent=2)
            except Exception as e:
                print(f"[SELF-HOST] Registry write error: {e}")

    # ============================================
    # CLEANUP
    # ============================================
    def cleanup_stale(self, max_age_seconds=3600, keep_latest=3):
        try:
            registry = self.list_deployments()
            now = time.time()
            removed = []

            sorted_deploys = sorted(
                registry.items(),
                key=lambda x: x[1].get('deployed_at', 0),
                reverse=True,
            )

            for idx, (deploy_id, data) in enumerate(sorted_deploys):
                age = now - data.get('deployed_at', now)
                status = data.get('status', 'unknown')

                if age > max_age_seconds and idx >= keep_latest:
                    self.delete_deployment(deploy_id)
                    removed.append(deploy_id)
                elif status == 'stopped' and age > 300:
                    self.delete_deployment(deploy_id)
                    removed.append(deploy_id)
                elif status == 'failed' and age > 600:
                    self.delete_deployment(deploy_id)
                    removed.append(deploy_id)

            try:
                valid_ids = set(registry.keys()) | {'_cache'}
                for folder in os.listdir(self.deploy_root):
                    folder_path = os.path.join(self.deploy_root, folder)
                    if os.path.isdir(folder_path) and folder not in valid_ids:
                        print(f"[SELF-HOST] Orphan: {folder} - deleting")
                        subprocess.run(f'rd /s /q "{folder_path}"', shell=True, capture_output=True, timeout=300)
                        removed.append(folder)
            except Exception:
                pass

            return {'success': True, 'removed': removed, 'remaining': len(self.list_deployments())}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    # ============================================
    # HELPERS
    # ============================================
    def _generate_deploy_id(self, owner, repo):
        slug = re.sub(r'[^a-z0-9\-]', '-', f"{owner}-{repo}".lower())[:40]
        short_hash = hashlib.md5(f"{owner}/{repo}{time.time()}".encode()).hexdigest()[:6]
        return f"{slug}-{short_hash}"

    def _inject_token(self, repo_url):
        token = os.getenv('GITHUB_TOKEN')
        if token and 'github.com' in repo_url:
            return repo_url.replace('https://github.com/', f'https://{token}@github.com/')
        return repo_url