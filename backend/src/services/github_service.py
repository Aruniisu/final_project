import os
import re
import base64
from datetime import datetime
import requests
from github import Github, GithubException
from github.GithubException import RateLimitExceededException
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self, token=None):
        self.token = token or os.getenv('GITHUB_ACCESS_TOKEN')
        self.client = Github(self.token) if self.token else None
        self.rate_limit_remaining = 0
    
    def is_authenticated(self):
        """Check if authenticated with GitHub"""
        return self.client is not None
    
    def get_rate_limit(self):
        """Get rate limit status"""
        if not self.client:
            return None
        try:
            rate = self.client.get_rate_limit()
            return {
                'core': {
                    'limit': rate.core.limit,
                    'remaining': rate.core.remaining,
                    'reset': rate.core.reset.isoformat()
                },
                'search': {
                    'limit': rate.search.limit,
                    'remaining': rate.search.remaining,
                    'reset': rate.search.reset.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting rate limit: {e}")
            return None
    
    def get_repository(self, repo_url):
        """Get repository from URL"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        # Parse URL
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            return {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'ssh_url': repo.ssh_url,
                'default_branch': repo.default_branch,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat(),
                'language': repo.language,
                'topics': repo.get_topics(),
                'size': repo.size,
                'private': repo.private
            }
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def get_repository_contents(self, repo_url, path='', branch=None):
        """Get repository contents"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            branch = branch or repo.default_branch
            
            contents = repo.get_contents(path, ref=branch)
            
            if isinstance(contents, list):
                # Directory
                result = []
                for content in contents:
                    result.append({
                        'name': content.name,
                        'path': content.path,
                        'type': content.type,
                        'size': content.size,
                        'sha': content.sha,
                        'url': content.html_url,
                        'download_url': content.download_url
                    })
                return result
            else:
                # Single file
                return {
                    'name': contents.name,
                    'path': contents.path,
                    'type': contents.type,
                    'size': contents.size,
                    'sha': contents.sha,
                    'url': contents.html_url,
                    'download_url': contents.download_url,
                    'content': base64.b64decode(contents.content).decode('utf-8') if contents.content else None
                }
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def clone_repository(self, repo_url, target_dir):
        """Clone repository to target directory"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        import subprocess
        
        try:
            # Use git clone
            clone_url = f"https://{self.token}@github.com/{repo_path}.git"
            cmd = ['git', 'clone', clone_url, target_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Clone failed: {result.stderr}")
            
            return target_dir
        except Exception as e:
            logger.error(f"Clone error: {e}")
            raise
    
    def create_repository(self, name, description='', private=False, auto_init=True):
        """Create a new repository"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        try:
            user = self.client.get_user()
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init
            )
            return {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url
            }
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def create_issue(self, repo_url, title, body=''):
        """Create an issue"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            issue = repo.create_issue(title=title, body=body)
            return {
                'id': issue.id,
                'number': issue.number,
                'title': issue.title,
                'url': issue.html_url,
                'state': issue.state
            }
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def create_pull_request(self, repo_url, title, body='', head='', base='main'):
        """Create a pull request"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            return {
                'id': pr.id,
                'number': pr.number,
                'title': pr.title,
                'url': pr.html_url,
                'state': pr.state,
                'mergeable': pr.mergeable
            }
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def get_branches(self, repo_url):
        """Get repository branches"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            branches = repo.get_branches()
            return [{
                'name': branch.name,
                'commit_sha': branch.commit.sha,
                'protected': branch.protected
            } for branch in branches]
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def get_commits(self, repo_url, branch='main', limit=10):
        """Get repository commits"""
        if not self.client:
            raise ValueError("GitHub client not authenticated")
        
        repo_path = self._parse_repo_url(repo_url)
        if not repo_path:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        try:
            repo = self.client.get_repo(repo_path)
            commits = repo.get_commits(sha=branch)[:limit]
            return [{
                'sha': commit.sha,
                'message': commit.commit.message,
                'author': commit.commit.author.name,
                'email': commit.commit.author.email,
                'date': commit.commit.author.date.isoformat(),
                'url': commit.html_url
            } for commit in commits]
        except GithubException as e:
            logger.error(f"GitHub error: {e}")
            raise
    
    def _parse_repo_url(self, url):
        """Parse GitHub repository URL"""
        # Handle different formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?$',
            r'github\.com/([^/]+)/([^/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        
        return None
    
    def webhook_payload_parser(self, payload):
        """Parse GitHub webhook payload"""
        event_type = payload.get('action', 'unknown')
        
        if 'pull_request' in payload:
            pr = payload['pull_request']
            return {
                'type': 'pull_request',
                'action': event_type,
                'number': pr.get('number'),
                'title': pr.get('title'),
                'url': pr.get('html_url'),
                'user': pr.get('user', {}).get('login'),
                'state': pr.get('state')
            }
        elif 'push' in payload:
            return {
                'type': 'push',
                'action': event_type,
                'ref': payload.get('ref'),
                'repository': payload.get('repository', {}).get('full_name'),
                'commits': len(payload.get('commits', [])),
                'pusher': payload.get('pusher', {}).get('name')
            }
        else:
            return {
                'type': 'unknown',
                'action': event_type,
                'payload': payload
            }