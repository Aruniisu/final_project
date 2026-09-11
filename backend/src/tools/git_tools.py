"""
Git Tools — Wrapper for git operations
Used by agents to interact with Git repositories.
"""

import os
import subprocess
from typing import Optional, List, Dict, Any


class GitTools:
    """Wrapper around git CLI commands."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getcwd()

    def _run(self, *args: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a git command and return result."""
        try:
            result = subprocess.run(
                ['git', *args],
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode,
            }
        except FileNotFoundError:
            return {'success': False, 'error': 'git not installed'}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'git command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def clone(self, url: str, dest: str, branch: str = 'main') -> Dict[str, Any]:
        """Clone a repository."""
        return self._run('clone', '--branch', branch, url, dest, cwd=os.getcwd())

    def pull(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('pull', cwd=cwd)

    def status(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('status', '--short', cwd=cwd)

    def add_all(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('add', '.', cwd=cwd)

    def commit(self, message: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('commit', '-m', message, cwd=cwd)

    def push(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('push', cwd=cwd)

    def current_branch(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('rev-parse', '--abbrev-ref', 'HEAD', cwd=cwd)

    def log(self, limit: int = 10, cwd: Optional[str] = None) -> Dict[str, Any]:
        return self._run('log', f'-{limit}', '--oneline', cwd=cwd)