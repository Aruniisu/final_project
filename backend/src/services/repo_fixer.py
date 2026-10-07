"""
RepoFixer — Fix ALL errors in any branch + create PR
=====================================================
Supports ANY branch (auto-detect default).
Uses GROQ_MODEL from .env — change model without touching code.
Broadcasts logs to frontend Live Logs via event_bus.
"""

import os
import re
import json
import time
import shutil
import tempfile
import subprocess
import requests
from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────
# LLM Config (env-driven, safe defaults)
# ─────────────────────────────────────────────
DEFAULT_GROQ_MODEL = 'openai/gpt-oss-120b'
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'


def _get_groq_model() -> str:
    """Read model from env, fall back to safe default."""
    return os.getenv('GROQ_MODEL', DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


class RepoFixer:
    """Fix repo errors + create PR (any branch)."""

    def __init__(self, agent=None):
        self.agent = agent
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.temp_root = os.path.join(tempfile.gettempdir(), 'repo_fixes')
        os.makedirs(self.temp_root, exist_ok=True)

        # Log the model at init time (helps debugging)
        self.groq_model = _get_groq_model()
        print(f"[FIXER] RepoFixer initialized — GROQ_MODEL={self.groq_model}", flush=True)

    # ──────────────────────────────────────────
    # GitHub API helpers
    # ──────────────────────────────────────────
    def _gh_headers(self):
        h = {'Accept': 'application/vnd.github+json'}
        if self.github_token:
            h['Authorization'] = f'token {self.github_token}'
        return h

    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch via GitHub API."""
        try:
            r = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=self._gh_headers(),
                timeout=10,
            )
            if r.status_code == 200:
                return r.json().get('default_branch', 'main')
        except Exception as e:
            print(f"[FIXER] default branch lookup failed: {e}", flush=True)
        return 'main'

    def list_branches(self, owner: str, repo: str) -> List[str]:
        """List all branches of the repo."""
        try:
            r = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/branches?per_page=100',
                headers=self._gh_headers(),
                timeout=10,
            )
            if r.status_code == 200:
                return [b['name'] for b in r.json()]
        except Exception as e:
            print(f"[FIXER] list_branches failed: {e}", flush=True)
        return []

    def branch_exists(self, owner: str, repo: str, branch: str) -> bool:
        """Check if branch exists."""
        return branch in self.list_branches(owner, repo)

    # ──────────────────────────────────────────
    # Git operations
    # ──────────────────────────────────────────
    def clone_repo(self, owner: str, repo: str, branch: str = None) -> Dict:
        """Clone repo at given branch (or default)."""
        if not branch:
            branch = self.get_default_branch(owner, repo)

        fix_id = f"{owner}-{repo}-{int(time.time())}"
        target = os.path.join(self.temp_root, fix_id)

        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)

        token = self.github_token
        clone_url = (
            f'https://{token}@github.com/{owner}/{repo}.git'
            if token else
            f'https://github.com/{owner}/{repo}.git'
        )

        try:
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--single-branch',
                 '-b', branch, clone_url, target],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Clone failed: {result.stderr[:300]}",
                    'branch': branch,
                }

            subprocess.run(
                ['git', 'config', 'user.email', 'bot@agentic-ai.dev'],
                cwd=target, capture_output=True, timeout=10,
            )
            subprocess.run(
                ['git', 'config', 'user.name', 'Agentic AI Bot'],
                cwd=target, capture_output=True, timeout=10,
            )

            return {'success': True, 'path': target, 'branch': branch}
        except Exception as e:
            return {'success': False, 'error': str(e)[:300], 'branch': branch}

    def create_branch(self, path: str, branch_name: str) -> bool:
        try:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=path, capture_output=True, text=True, timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def commit_changes(self, path: str, message: str, branch: str) -> Dict:
        try:
            subprocess.run(['git', 'add', '-A'], cwd=path,
                           capture_output=True, timeout=60)

            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=path, capture_output=True, text=True, timeout=60,
            )

            if result.returncode != 0:
                return {'success': False, 'error': result.stderr[:200]}

            push_result = subprocess.run(
                ['git', 'push', '-u', 'origin', branch],
                cwd=path, capture_output=True, text=True, timeout=120,
            )

            if push_result.returncode != 0:
                return {'success': False, 'error': push_result.stderr[:200]}

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)[:200]}

    def create_pr(self, owner, repo, head, base, title, body) -> Dict:
        if not self.github_token:
            return {'success': False, 'error': 'GITHUB_TOKEN not set'}

        try:
            r = requests.post(
                f'https://api.github.com/repos/{owner}/{repo}/pulls',
                headers=self._gh_headers(),
                json={
                    'title': title,
                    'head': head,
                    'base': base,
                    'body': body,
                },
                timeout=30,
            )

            if r.status_code not in (200, 201):
                return {'success': False, 'error': r.text[:300]}

            data = r.json()
            return {
                'success': True,
                'pr_url': data.get('html_url'),
                'pr_number': data.get('number'),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)[:300]}

    # ──────────────────────────────────────────
    # LLM fix — env-driven model + detailed logging
    # ──────────────────────────────────────────
    def fix_file_with_llm(self, filepath, content, issues, log):
        """Fix a file using LLM (with detailed logging)."""
        try:
            issues_desc = '\n'.join([
                f"- Line {i.get('line', '?')}: {i.get('message', 'unknown')}"
                for i in issues[:10]
            ])

            prompt_parts = [
                "Fix ALL errors in this code. Return ONLY the fixed code, no explanation.",
                "",
                "Issues found:",
                issues_desc,
                "",
                "Code:",
                "```",
                content,
                "```",
                "",
                "Return ONLY the fixed code, no markdown fences, no explanation.",
            ]
            prompt = '\n'.join(prompt_parts)

            response = None

            # ── Path A: use agent's LLM if available ──
            if self.agent and hasattr(self.agent, 'call_llm'):
                log("      → Trying agent.call_llm()")
                try:
                    response = self.agent.call_llm(prompt)
                except Exception as e:
                    log(f"      ✗ agent.call_llm failed: {str(e)[:200]}")

            # ── Path B: fall back to Groq API directly ──
            if not response:
                groq_key = os.getenv('GROQ_API_KEY')
                if not groq_key:
                    log("      ✗ GROQ_API_KEY not set in .env!")
                    return None

                model = _get_groq_model()
                log(f"      → Calling Groq API (model: {model}, key: {groq_key[:8]}...)")

                try:
                    r = requests.post(
                        GROQ_API_URL,
                        headers={
                            'Authorization': f'Bearer {groq_key}',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'model': model,
                            'messages': [{'role': 'user', 'content': prompt}],
                            'temperature': 0.1,
                            'max_tokens': 4000,
                        },
                        timeout=60,
                    )

                    if r.status_code != 200:
                        log(f"      ✗ Groq API error {r.status_code}: {r.text[:200]}")
                        if r.status_code == 404:
                            log("      💡 Hint: model may be deprecated. "
                                "Try GROQ_MODEL=openai/gpt-oss-120b or llama-3.1-8b-instant")
                        elif r.status_code == 401:
                            log("      💡 Hint: invalid GROQ_API_KEY. Check .env")
                        elif r.status_code == 429:
                            log("      💡 Hint: rate limited. Wait a few seconds.")
                        return None

                    data = r.json()
                    response = data['choices'][0]['message']['content']
                    log(f"      ✓ Groq responded ({len(response)} chars)")
                except Exception as e:
                    log(f"      ✗ Groq request failed: {str(e)[:200]}")
                    return None

            if not response:
                log("      ✗ LLM returned empty response")
                return None

            # Strip markdown fences if present
            response = response.strip()
            response = re.sub(r'^```(?:\w+)?\s*\n?', '', response)
            response = re.sub(r'\n?```\s*$', '', response)
            response = response.strip()

            # Check if actually different
            if response == content.strip():
                log("      ⚠ LLM returned identical code (no fix needed?)")
                return None

            return response

        except Exception as e:
            log(f"      ✗ LLM fix error: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            return None

    # ──────────────────────────────────────────
    # Main fix
    # ──────────────────────────────────────────
    def fix_repo(self, owner, repo, branch=None, on_log=None) -> Dict:
        def log(msg, level='info'):
            # 1) Local print (backend terminal)
            try:
                print(f"[FIXER] {msg}", flush=True)
            except Exception:
                pass

            # 2) Optional callback (devops.py on_log)
            if on_log:
                try:
                    on_log(msg, level)
                except Exception:
                    pass

            # 3) ⭐ Event Bus → frontend Live Logs
            try:
                from core.event_bus import emit_event
                emit_event('fixer:log', {
                    'message': f"[FIXER] {msg}",
                    'level': level,
                    'source': 'repo_fixer',
                })
            except Exception:
                pass

            # 4) ⭐ Also push directly to live_log channel
            try:
                from core.event_bus import _socketio
                if _socketio:
                    _socketio.emit('live_log', {
                        'log': f"[FIXER] {msg}",
                        'message': f"[FIXER] {msg}",
                        'type': level,
                        'level': level,
                        'timestamp': time.strftime("%H:%M:%S"),
                        'source': 'fixer',
                    })
            except Exception:
                pass

        # Auto-detect branch if not given
        if not branch:
            branch = self.get_default_branch(owner, repo)
            log(f"Auto-detected default branch: {branch}")

        # Verify branch exists
        if not self.branch_exists(owner, repo, branch):
            log(f"⚠️  Branch '{branch}' not found — falling back to default")
            branch = self.get_default_branch(owner, repo)

        log(f"Cloning {owner}/{repo} @ {branch}...")
        clone_result = self.clone_repo(owner, repo, branch)
        if not clone_result.get('success'):
            return {'success': False, 'error': clone_result.get('error')}

        repo_path = clone_result['path']

        try:
            log(f"Scanning for errors...")
            from .repo_scanner import repo_scanner
            scan_result = repo_scanner.scan(repo_path)

            total = scan_result.get('total_issues', 0)
            log(f"   Found {total} issues ({scan_result.get('critical', 0)} critical)")

            if total == 0:
                return {
                    'success': True,
                    'message': 'No issues found',
                    'total_issues': 0,
                    'files_fixed': [],
                    'branch': branch,
                }

            issues_by_file = {}
            for issue in scan_result.get('issues', []):
                f = issue.get('file')
                issues_by_file.setdefault(f, []).append(issue)

            branch_name = f'auto-fix-{int(time.time())}'
            log(f"Creating branch: {branch_name}")
            if not self.create_branch(repo_path, branch_name):
                return {'success': False, 'error': 'Branch creation failed'}

            files_fixed = []
            for relpath, file_issues in list(issues_by_file.items())[:10]:
                filepath = os.path.join(repo_path, relpath)
                if not os.path.exists(filepath):
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        original = f.read()

                    log(f"   Fixing {relpath} ({len(file_issues)} issues)...")

                    fixed = self.fix_file_with_llm(filepath, original, file_issues, log)

                    if fixed and fixed != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(fixed)
                        files_fixed.append({
                            'file': relpath,
                            'issues': len(file_issues),
                        })
                        log(f"   ✓ Fixed {relpath}", 'success')
                    else:
                        log(f"   ✗ No fix for {relpath}", 'warning')
                except Exception as e:
                    log(f"   ✗ Error fixing {relpath}: {str(e)[:100]}", 'error')

            if not files_fixed:
                return {
                    'success': False,
                    'error': 'No files could be fixed (LLM failed on all files)',
                    'branch': branch,
                }

            log(f"Committing {len(files_fixed)} files...")
            commit_msg = f"chore: auto-fix {sum(f['issues'] for f in files_fixed)} issues"
            commit_result = self.commit_changes(repo_path, commit_msg, branch_name)

            if not commit_result.get('success'):
                return {'success': False, 'error': commit_result.get('error')}

            log(f"Creating PR ({branch_name} → {branch})...")
            fixed_files_list = '\n'.join([
                f"- `{f['file']}` ({f['issues']} issues)"
                for f in files_fixed
            ])
            total_fixed = sum(f['issues'] for f in files_fixed)

            pr_body_parts = [
                "## Auto-fix by Agentic AI",
                "",
                f"**Target branch:** `{branch}`",
                f"**Fixed files ({len(files_fixed)}):**",
                fixed_files_list,
                "",
                f"**Total issues fixed:** {total_fixed}",
                "",
                "---",
                "",
                "*Generated by Smart DevOps Assistant*",
            ]
            pr_body = '\n'.join(pr_body_parts)

            pr_result = self.create_pr(
                owner, repo,
                head=branch_name,
                base=branch,
                title=f"Auto-fix: {total_fixed} issues",
                body=pr_body,
            )

            if not pr_result.get('success'):
                log(f"PR failed: {pr_result.get('error')}", 'error')
                return {
                    'success': True,
                    'message': f'Fixed {len(files_fixed)} files (PR failed)',
                    'branch': branch_name,
                    'base_branch': branch,
                    'files_fixed': files_fixed,
                    'pr_url': None,
                    'pr_error': pr_result.get('error'),
                }

            log(f"PR created: {pr_result.get('pr_url')}", 'success')

            return {
                'success': True,
                'message': f'Fixed {total_fixed} issues in {len(files_fixed)} files',
                'branch': branch_name,
                'base_branch': branch,
                'files_fixed': files_fixed,
                'pr_url': pr_result.get('pr_url'),
                'pr_number': pr_result.get('pr_number'),
            }
        finally:
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
            except Exception:
                pass


repo_fixer = RepoFixer()