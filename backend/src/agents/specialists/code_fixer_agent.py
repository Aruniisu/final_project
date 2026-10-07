"""
CodeFixerAgent — Dual Mode
1. Chat mode: fix user-pasted code snippets
2. Repo mode: fix entire repo + create PR (uses repo_fixer as tool)
"""
import re
import json
import time
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent


def _parse_github_url(url: str):
    if not url:
        return None, None, None
    raw = url.strip().rstrip('/')
    if raw.endswith('.git'):
        raw = raw[:-4]
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?', raw)
    if m:
        return m.group(1), m.group(2), (m.group(3) or 'main')
    return None, None, None


class CodeFixerAgent(BaseAgent):
    """Code fixer — handles both chat snippets and repo-wide fixes."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'CodeFixerAgent',
            config={
                **(config or {}),
                'role': 'code fixing specialist',
                'goal': 'Fix user code snippets and repo-wide errors',
                'capabilities': ['fix_snippet', 'fix_repo', 'create_pr'],
                'max_retries': 2,
            }
        )
        self.total_fixes = 0
        self.successful_fixes = 0
        self.failed_fixes = 0

    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        sid = context.get('sid') if context else None

        if not isinstance(input_data, dict):
            input_data = {'query': str(input_data)}

        # Detect mode
        repo_url = input_data.get('repo_url') or input_data.get('repoUrl')
        code = input_data.get('code', '')
        query = input_data.get('query', '')

        # Try extracting URL from query
        if not repo_url and query:
            m = re.search(r'https?://github\.com/\S+', query)
            if m:
                repo_url = m.group(0)

        # If repo URL → repo mode
        if repo_url:
            return self._fix_repo_mode(repo_url, input_data.get('branch'), sid)

        # Otherwise → chat snippet mode
        if not code:
            code = self._extract_code_from_message(query)
        return self._fix_snippet_mode(code, input_data.get('error', ''), query, sid)

    # ═══════════════════════════════════════════
    # REPO MODE
    # ═══════════════════════════════════════════
    def _fix_repo_mode(self, repo_url, branch_override, sid) -> Dict:
        owner, repo, branch = _parse_github_url(repo_url)
        if not owner:
            return self._error_response("Invalid GitHub URL", sid)
        if branch_override:
            branch = branch_override

        self.emit_log("=" * 60, "info", sid)
        self.emit_log(f"🔧 CodeFixerAgent (repo mode)", "info", sid)
        self.emit_log(f"   Repo: {owner}/{repo}", "info", sid)
        self.emit_log(f"   Branch: {branch}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        start = time.time()
        try:
            from services.repo_fixer import repo_fixer

            def on_log(msg, level='info'):
                self.emit_log(f"   {msg}", level, sid)
                self._emit_chat_log(sid, f"[FIXER] {msg}")

            result = repo_fixer.fix_repo(owner, repo, branch=branch, on_log=on_log)

            elapsed = time.time() - start
            self.total_fixes += 1

            if result.get('success'):
                self.successful_fixes += 1
                self.track_metric(True, elapsed)
                response_md = self._build_repo_response_md(owner, repo, branch, result, elapsed)
                self._emit_chat(sid, response_md)
                return {
                    'success': True,
                    'type': 'code_fix_repo',
                    'status': 'completed',
                    'branch': branch,
                    'pr_url': result.get('pr_url'),
                    'files_fixed': result.get('files_fixed', []),
                    'duration': f'{elapsed:.1f}s',
                    'response': response_md,
                    'result': result,
                }
            else:
                self.failed_fixes += 1
                self.track_metric(False, elapsed)
                return self._error_response(result.get('error', 'Fix failed'), sid)
        except Exception as e:
            elapsed = time.time() - start
            self.failed_fixes += 1
            self.track_metric(False, elapsed)
            self.emit_log(f"❌ Repo fix failed: {str(e)[:200]}", "error", sid)
            import traceback
            traceback.print_exc()
            return self._error_response(str(e), sid)

    def _build_repo_response_md(self, owner, repo, branch, result, elapsed) -> str:
        parts = ["## 🔧 Repo Fix Complete", ""]
        parts.append(f"**Repo:** `{owner}/{repo}`")
        parts.append(f"**Branch:** `{branch}`")
        parts.append(f"**Time:** {elapsed:.1f}s")
        parts.append("")

        files = result.get('files_fixed', [])
        if files:
            parts.append(f"### ✅ Fixed {len(files)} file(s)")
            for f in files:
                parts.append(f"- `{f.get('file')}` ({f.get('issues', 0)} issues)")
            parts.append("")

        pr_url = result.get('pr_url')
        if pr_url:
            parts.append(f"### 🎉 Pull Request Created")
            parts.append(f"[{pr_url}]({pr_url})")
        elif result.get('message') == 'No issues found':
            parts.append("### ✅ No issues found — repo is clean!")
        else:
            parts.append(f"**Note:** {result.get('message', '')}")

        parts.append("")
        parts.append("*Fixed by CodeFixerAgent*")
        return '\n'.join(parts)

    # ═══════════════════════════════════════════
    # SNIPPET MODE (chat)
    # ═══════════════════════════════════════════
    def _fix_snippet_mode(self, code, error, query, sid) -> Dict:
        self.emit_log("=" * 60, "info", sid)
        self.emit_log(f"🔧 CodeFixerAgent (chat mode)", "info", sid)
        self.emit_log(f"   Code size: {len(code) if code else 0} chars", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        if not code:
            return self._error_response(
                "No code found. Paste code in ```language...``` block.", sid
            )

        language = self._detect_language(code)
        start = time.time()

        try:
            fix_result = self._fix_code_llm(code, error, language, sid)
            if not fix_result:
                self.failed_fixes += 1
                return self._error_response("LLM returned no valid response", sid)

            elapsed = time.time() - start
            self.total_fixes += 1
            self.successful_fixes += 1
            self.track_metric(True, elapsed)

            response_md = self._build_snippet_response_md(fix_result, language, error)
            self._emit_chat(sid, response_md)

            return {
                'success': True,
                'type': 'code_fix_snippet',
                'status': 'fixed',
                'language': language,
                'fixed_code': fix_result.get('fixed_code', ''),
                'response': response_md,
            }
        except Exception as e:
            elapsed = time.time() - start
            self.failed_fixes += 1
            self.track_metric(False, elapsed)
            return self._error_response(str(e), sid)

    def _extract_code_from_message(self, message: str) -> str:
        if not message:
            return ''
        m = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', message, re.DOTALL)
        if m:
            return m.group(1).strip()
        return ''

    def _detect_language(self, code: str) -> str:
        if not code:
            return 'text'
        cl = code.lower()
        if 'def ' in code and ':' in code:
            return 'python'
        if 'function ' in cl or 'const ' in cl or '=>' in code:
            return 'javascript'
        if 'interface ' in cl or ': string' in cl:
            return 'typescript'
        if 'public class' in cl:
            return 'java'
        return 'python'

    def _fix_code_llm(self, code, error, language, sid) -> Optional[Dict]:
        system_msg = (
            f"You are an expert {language} code fixer. "
            "Return ONLY valid JSON. No markdown."
        )
        prompt_parts = [
            f"Language: {language}", "",
            f"Error: {error}" if error else "", "",
            "Code to fix:", "```", code[:6000], "```", "",
            "Return ONLY JSON with keys:",
            '{"fixed_code": "...", "root_cause": "...", "explanation": "...", "issues": [{"type": "bug|style", "description": "..."}]}',
        ]
        prompt = '\n'.join(p for p in prompt_parts if p is not None)

        response = self.call_llm(prompt, system_prompt=system_msg, temperature=0.1, max_tokens=4000)
        if not response:
            return None

        try:
            cleaned = re.sub(r'^```(?:json)?\s*', '', response)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    return None
            return None

    def _build_snippet_response_md(self, fix_result, language, error) -> str:
        parts = ["## 🔧 Code Fixed", ""]
        if error:
            parts.append(f"**Error:** `{error}`")
            parts.append("")
        root = fix_result.get('root_cause', '')
        if root:
            parts.append(f"### 🐛 Root Cause")
            parts.append(root)
            parts.append("")
        issues = fix_result.get('issues', [])
        if issues:
            parts.append(f"### ⚠️ Issues ({len(issues)})")
            for i in issues[:5]:
                parts.append(f"- **{i.get('type', 'issue')}**: {i.get('description', '')}")
            parts.append("")
        explanation = fix_result.get('explanation', '')
        if explanation:
            parts.append("### 📝 Explanation")
            parts.append(explanation)
            parts.append("")
        parts.append("### ✅ Fixed Code")
        parts.append(f"```{language}")
        parts.append(fix_result.get('fixed_code', ''))
        parts.append("```")
        parts.append("")
        parts.append("*Fixed by CodeFixerAgent*")
        return '\n'.join(parts)

    # ═══════════════════════════════════════════
    # Shared helpers
    # ═══════════════════════════════════════════
    def _emit_chat(self, sid, markdown):
        try:
            from core.event_bus import _socketio
            if _socketio:
                payload = {
                    'message': markdown,
                    'source': 'CodeFixerAgent',
                    'type': 'code_fix',
                    'timestamp': time.strftime('%H:%M:%S'),
                }
                if sid:
                    _socketio.emit('chat_response', payload, room=sid)
                else:
                    _socketio.emit('chat_response', payload)
        except Exception:
            pass

    def _emit_chat_log(self, sid, msg):
        try:
            from core.event_bus import emit_event
            emit_event('fixer:log', {'message': msg, 'source': 'code_fixer'})
        except Exception:
            pass

    def _error_response(self, msg, sid=None):
        response = f"## ❌ Failed\n\n**Error:** {msg}"
        self._emit_chat(sid, response)
        return {'success': False, 'error': msg, 'response': response}

    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {**base, 'total_fixes': self.total_fixes,
                'successful_fixes': self.successful_fixes,
                'failed_fixes': self.failed_fixes}