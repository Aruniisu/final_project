"""
Process Manager — Self-Hosted App Runtime (No Docker)
========================================================
Location: src/core/process_manager.py
Apps folder: src/deployed_apps/
"""

import os
import sys
import json
import time
import signal
import socket
import platform
import subprocess
import threading
import shutil
import psutil
from pathlib import Path
from typing import Optional, Dict, List

IS_WINDOWS = platform.system() == 'Windows'

# ============================================
# PATHS
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent   # src/
APPS_DIR = BASE_DIR / 'deployed_apps'
LOGS_DIR = APPS_DIR / '_logs'
REGISTRY = APPS_DIR / '_registry.json'
PORT_RANGE = (8100, 8999)

APPS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 ProcessManager paths:")
print(f"   APPS_DIR:  {APPS_DIR}")
print(f"   LOGS_DIR:  {LOGS_DIR}")


# ============================================
# APP PROCESS
# ============================================
class AppProcess:
    def __init__(self, name, path, command, port, env=None):
        self.name = name
        self.path = path
        self.command = command
        self.port = port
        self.env = env or {}
        self.process: Optional[subprocess.Popen] = None
        self.started_at = None
        self.crashes = 0
        self.status = 'stopped'

    def to_dict(self):
        proc = self.process
        pid = proc.pid if proc else None
        alive = bool(proc and proc.poll() is None)
        return {
            'service_name': self.name,
            'display_name': self.name,
            'path': self.path,
            'command': self.command,
            'port': self.port,
            'pid': pid,
            'status': 'running' if alive else self.status,
            'started_at': self.started_at,
            'crashes': self.crashes,
            'uptime_seconds': round((time.time() - self.started_at), 1) if self.started_at else 0,
            'cpu_percent': self._cpu(),
            'memory_percent': self._mem(),
            'memory_mb': self._mem_mb(),
            'live_url': f'http://localhost:{self.port}',
            'replicas': 1,
            'requests_per_sec': 0,
            'source': 'process-manager',
            'image': 'python-process',
            'id': f'proc-{self.name}-{self.port}',
        }

    def _proc(self):
        try:
            if self.process and self.process.poll() is None:
                return psutil.Process(self.process.pid)
        except Exception:
            pass
        return None

    def _cpu(self):
        p = self._proc()
        try:
            return round(p.cpu_percent(interval=0.05), 1) if p else 0
        except Exception:
            return 0

    def _mem(self):
        p = self._proc()
        try:
            return round(p.memory_percent(), 1) if p else 0
        except Exception:
            return 0

    def _mem_mb(self):
        p = self._proc()
        try:
            return round(p.memory_info().rss / 1_000_000, 1) if p else 0
        except Exception:
            return 0


# ============================================
# PROCESS MANAGER
# ============================================
class ProcessManager:
    def __init__(self):
        self.apps: Dict[str, AppProcess] = {}
        self._lock = threading.Lock()
        self._load_registry()

    def _load_registry(self):
        try:
            if REGISTRY.exists():
                data = json.loads(REGISTRY.read_text(encoding='utf-8'))
                for item in data.get('apps', []):
                    app = AppProcess(
                        item['name'], item['path'],
                        item['command'], item['port']
                    )
                    self.apps[app.name] = app
                print(f"📦 Loaded {len(self.apps)} apps from registry")
        except Exception as e:
            print(f"⚠️  Registry load failed: {e}")

    def _save_registry(self):
        try:
            data = {'apps': [
                {'name': a.name, 'path': a.path,
                 'command': a.command, 'port': a.port}
                for a in self.apps.values()
            ]}
            REGISTRY.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Registry save failed: {e}")

    def _port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(('127.0.0.1', port)) == 0

    def _find_free_port(self):
        used = {a.port for a in self.apps.values()}
        for p in range(PORT_RANGE[0], PORT_RANGE[1]):
            if p not in used and not self._port_in_use(p):
                return p
        raise RuntimeError("No free ports available")

    def start_app(self, name):
        with self._lock:
            app = self.apps.get(name)
            if not app:
                return {'success': False, 'error': f'{name} not registered'}
            if app.process and app.process.poll() is None:
                return {'success': False, 'error': f'{name} already running'}
            if not os.path.isdir(app.path):
                app.status = 'failed'
                return {'success': False, 'error': f'Path not found: {app.path}'}

            log_file = LOGS_DIR / f'{name}_{int(time.time())}.log'
            try:
                log_handle = open(log_file, 'w', encoding='utf-8', errors='ignore')
                env = {**os.environ, **app.env, 'PORT': str(app.port)}

                popen_kwargs = {
                    'shell': True,
                    'cwd': app.path,
                    'stdout': log_handle,
                    'stderr': subprocess.STDOUT,
                    'env': env,
                }
                if IS_WINDOWS:
                    popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    popen_kwargs['preexec_fn'] = os.setsid

                app.process = subprocess.Popen(app.command, **popen_kwargs)
                app.started_at = time.time()
                app.status = 'starting'

                time.sleep(2)

                if app.process.poll() is None:
                    app.status = 'running'
                    print(f"✅ Started {name} (PID {app.process.pid}) on :{app.port}")
                    return {
                        'success': True,
                        'name': name,
                        'pid': app.process.pid,
                        'port': app.port,
                        'url': f'http://localhost:{app.port}',
                        'log_file': str(log_file),
                    }
                else:
                    app.status = 'crashed'
                    app.crashes += 1
                    return {'success': False, 'error': 'App crashed on startup',
                            'log_file': str(log_file)}
            except Exception as e:
                app.status = 'failed'
                return {'success': False, 'error': str(e)}

    def _kill_tree(self, proc):
        try:
            if IS_WINDOWS:
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            else:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def stop_app(self, name):
        with self._lock:
            app = self.apps.get(name)
            if not app or not app.process:
                return {'success': False, 'error': f'{name} not running'}
            try:
                if app.process.poll() is None:
                    self._kill_tree(app.process)
                app.process = None
                app.status = 'stopped'
                app.started_at = None
                print(f"🛑 Stopped {name}")
                return {'success': True, 'name': name}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def restart_app(self, name):
        self.stop_app(name)
        time.sleep(1)
        return self.start_app(name)

    def register_app(self, name, path, command, port=None):
        with self._lock:
            if name in self.apps:
                return {'success': False, 'error': f'{name} already registered'}
            if not port:
                port = self._find_free_port()
            self.apps[name] = AppProcess(name, path, command, port)
            self._save_registry()
            print(f"📝 Registered {name} → {path} :{port}")
            return {'success': True, 'name': name, 'port': port}

    def unregister_app(self, name, delete_files=False):
        with self._lock:
            app = self.apps.get(name)
            if not app:
                return {'success': False, 'error': 'Not found'}
            self.stop_app(name)
            if delete_files:
                shutil.rmtree(app.path, ignore_errors=True)
            del self.apps[name]
            self._save_registry()
            return {'success': True}

    def list_apps(self):
        for a in self.apps.values():
            if a.process:
                rc = a.process.poll()
                if rc is None:
                    a.status = 'running'
                elif a.status != 'stopped':
                    a.status = 'crashed'
        return [a.to_dict() for a in self.apps.values()]

    def get_app(self, name):
        app = self.apps.get(name)
        return app.to_dict() if app else None

    def health_check(self, name, path='/'):
        app = self.apps.get(name)
        if not app or not app.process or app.process.poll() is not None:
            return {'healthy': False, 'reason': 'not running'}
        try:
            import urllib.request
            url = f'http://localhost:{app.port}{path}'
            start = time.time()
            with urllib.request.urlopen(url, timeout=5) as r:
                status = r.status
            return {
                'healthy': 200 <= status < 400,
                'status_code': status,
                'response_ms': round((time.time() - start) * 1000, 1),
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}

    def stop_all(self):
        for name in list(self.apps.keys()):
            try:
                self.stop_app(name)
            except Exception:
                pass


# Singleton
manager = ProcessManager()