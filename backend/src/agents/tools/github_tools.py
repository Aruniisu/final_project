"""
GitHub Tools
Real GitHub API operations for agents.
"""

import os
import re
import base64
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional, List

import requests


def register_github_tools(registry, agent):
    """Register all GitHub tools with the agent's tool registry."""

    # ============================================
    # Tool 1: Parse GitHub URL
    # ============================================
    @registry.register_tool(
        name='github_parse_url',
        description='Parse a GitHub URL and extract owner and repo name',
        parameters={
            'url': {'type': 'string', 'description': 'GitHub repository URL'},
        },
    )
    def github_parse_url(url: str) -> Dict:
        """Extract (owner, repo) from GitHub URL."""
        patterns = [
            r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/\s\.]+?)(?:\.git)?$',
        ]
        for pattern in patterns:
            match = re.match(pattern, url.strip())
            if match:
                return {
                    'success': True,
                    'owner': match.group(1),
                    'repo': match.group(2),
                }
        return {'success': False, 'error': f'Invalid GitHub URL: {url}'}

    # ============================================
    # Tool 2: Get repo info
    # ============================================
    @registry.register_tool(
        name='github_get_repo_info',
        description='Get repository metadata (id, branch, description) from GitHub',
        parameters={
            'owner': {'type': 'string', 'description': 'Repo owner'},
            'repo': {'type': 'string', 'description': 'Repo name'},
        },
    )
    def github_get_repo_info(owner: str, repo: str) -> Dict:
        """Fetch repo metadata from GitHub API."""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            return {'success': False, 'error': 'GITHUB_TOKEN not set'}

        try:
            url = f'https://api.github.com/repos/{owner}/{repo}'
            response = requests.get(
                url,
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'id': data.get('id'),
                    'full_name': data.get('full_name'),
                    'default_branch': data.get('default_branch', 'main'),
                    'description': data.get('description'),
                    'language': data.get('language'),
                    'size': data.get('size'),
                    'private': data.get('private'),
                }

            return {
                'success': False,
                'error': f'GitHub API {response.status_code}: {response.text[:200]}',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 3: Clone repo
    # ============================================
    @registry.register_tool(
        name='github_clone',
        description='Clone a GitHub repository to a temp directory. Returns the local path.',
        parameters={
            'owner': {'type': 'string', 'description': 'Repo owner'},
            'repo': {'type': 'string', 'description': 'Repo name'},
            'branch': {'type': 'string', 'description': 'Branch to clone (default: main)'},
        },
    )
    def github_clone(owner: str, repo: str, branch: str = 'main') -> Dict:
        """Clone a GitHub repository."""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            return {'success': False, 'error': 'GITHUB_TOKEN not set'}

        try:
            tmp_dir = tempfile.mkdtemp(prefix='agent_clone_')
            clone_url = f'https://{token}@github.com/{owner}/{repo}.git'

            result = subprocess.run(
                ['git', 'clone', '--depth=1', '--branch', branch, clone_url, tmp_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                err = result.stderr.replace(token, '***')
                shutil.rmtree(tmp_dir, ignore_errors=True)
                return {'success': False, 'error': f'Clone failed: {err[:300]}'}

            return {
                'success': True,
                'path': tmp_dir,
                'owner': owner,
                'repo': repo,
                'branch': branch,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 4: Get files list
    # ============================================
    @registry.register_tool(
        name='github_get_files',
        description='Get list of files in a GitHub repository',
        parameters={
            'owner': {'type': 'string', 'description': 'Repo owner'},
            'repo': {'type': 'string', 'description': 'Repo name'},
            'path': {'type': 'string', 'description': 'Path within repo (optional)'},
        },
    )
    def github_get_files(owner: str, repo: str, path: str = '') -> Dict:
        """Get list of files in repo."""
        token = os.getenv('GITHUB_TOKEN')
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
            response = requests.get(
                url,
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            if response.status_code == 200:
                items = response.json()
                return {
                    'success': True,
                    'files': [
                        {
                            'name': item['name'],
                            'path': item['path'],
                            'type': item['type'],
                            'size': item.get('size', 0),
                        }
                        for item in items
                    ],
                }

            return {'success': False, 'error': f'GitHub API {response.status_code}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 5: Get file content
    # ============================================
    @registry.register_tool(
        name='github_get_file_content',
        description='Get the content of a specific file in a GitHub repo',
        parameters={
            'owner': {'type': 'string', 'description': 'Repo owner'},
            'repo': {'type': 'string', 'description': 'Repo name'},
            'path': {'type': 'string', 'description': 'File path in repo'},
        },
    )
    def github_get_file_content(owner: str, repo: str, path: str) -> Dict:
        """Get content of a file."""
        token = os.getenv('GITHUB_TOKEN')
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
            response = requests.get(
                url,
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                return {
                    'success': True,
                    'content': content,
                    'sha': data.get('sha'),
                    'size': data.get('size'),
                }

            return {'success': False, 'error': f'GitHub API {response.status_code}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================
    # Tool 6: Commit file
    # ============================================
    @registry.register_tool(
        name='github_commit_file',
        description='Create or update a file in a GitHub repo',
        parameters={
            'owner': {'type': 'string', 'description': 'Repo owner'},
            'repo': {'type': 'string', 'description': 'Repo name'},
            'path': {'type': 'string', 'description': 'File path in repo'},
            'content': {'type': 'string', 'description': 'New file content'},
            'message': {'type': 'string', 'description': 'Commit message'},
            'branch': {'type': 'string', 'description': 'Branch (default: main)'},
        },
    )
    def github_commit_file(
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str = 'Auto-commit',
        branch: str = 'main',
    ) -> Dict:
        """Create or update a file in GitHub."""
        token = os.getenv('GITHUB_TOKEN')
        try:
            # Check if file exists (to get SHA)
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
            existing = requests.get(
                url,
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )

            encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            payload = {
                'message': message,
                'content': encoded,
                'branch': branch,
            }

            if existing.status_code == 200:
                payload['sha'] = existing.json()['sha']

            response = requests.put(
                url,
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                json=payload,
                timeout=20,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    'success': True,
                    'commit_sha': data['commit']['sha'],
                    'html_url': data['commit']['html_url'],
                }

            return {
                'success': False,
                'error': f'GitHub API {response.status_code}: {response.text[:200]}',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    print(f"[GITHUB-TOOLS] Registered 6 tools for agent: {agent.name}")