"""
Docker Tools — Wrapper for Docker operations
Used by agents to build and deploy containers.
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List


class DockerTools:
    """Wrapper around Docker CLI / Kaniko for daemonless builds."""

    def __init__(self, registry: Optional[str] = None):
        self.registry = registry or os.getenv('DOCKER_REGISTRY', '')
        self.remote_host = os.getenv('DOCKER_HOST', None)

    def _run(self, *args: str, timeout: int = 300) -> Dict[str, Any]:
        """Run a docker command."""
        try:
            result = subprocess.run(
                ['docker', *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **({'DOCKER_HOST': self.remote_host} if self.remote_host else {})},
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
            }
        except FileNotFoundError:
            return {'success': False, 'error': 'docker CLI not installed'}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'docker command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def build(self, path: str = '.', tag: str = 'app:latest',
              dockerfile: str = 'Dockerfile') -> Dict[str, Any]:
        """Build a Docker image."""
        return self._run('build', '-t', tag, '-f', dockerfile, path)

    def push(self, tag: str) -> Dict[str, Any]:
        """Push an image to registry."""
        return self._run('push', tag)

    def run(self, image: str, name: Optional[str] = None,
            ports: Optional[List[str]] = None, detach: bool = True) -> Dict[str, Any]:
        """Run a container."""
        args = ['run']
        if detach:
            args.append('-d')
        if name:
            args.extend(['--name', name])
        if ports:
            for p in ports:
                args.extend(['-p', p])
        args.append(image)
        return self._run(*args)

    def stop(self, container: str) -> Dict[str, Any]:
        return self._run('stop', container)

    def remove(self, container_or_image: str, force: bool = False) -> Dict[str, Any]:
        args = ['rm']
        if force:
            args.append('-f')
        args.append(container_or_image)
        return self._run(*args)

    def list_containers(self, all: bool = False) -> Dict[str, Any]:
        args = ['ps', '--format', '{{json .}}']
        if all:
            args.append('-a')
        return self._run(*args)

    def list_images(self) -> Dict[str, Any]:
        return self._run('images', '--format', '{{json .}}')

    def inspect(self, target: str) -> Dict[str, Any]:
        result = self._run('inspect', target)
        if result['success']:
            try:
                result['data'] = json.loads(result['stdout'])
            except Exception:
                pass
        return result

    def is_available(self) -> bool:
        """Check if Docker is available locally."""
        result = self._run('version', '--format', '{{.Server.Version}}', timeout=10)
        return result.get('success', False)