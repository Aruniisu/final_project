"""
SecurityAgent — Real Security Scanner + LLM Analysis
=====================================================
Uses security_scanner.py as a TOOL.

Features:
- Single branch scan
- ⭐ ALL branches scan (combined report)
- LLM-powered analysis
- Chat-friendly markdown output
"""

import os
import re
import json
import time
import requests
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent


# ─────────────────────────────────────────────
DEFAULT_GROQ_MODEL = 'openai/gpt-oss-120b'
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'


def _get_groq_model() -> str:
    return os.getenv('GROQ_MODEL', DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def _parse_github_url(url: str):
    """Parse GitHub URL → (owner, repo, branch)."""
    if not url:
        return None, None, None

    raw = url.strip().rstrip('/')
    if raw.endswith('.git'):
        raw = raw[:-4]

    m = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?',
        raw
    )
    if m:
        return m.group(1), m.group(2), (m.group(3) or None)
    return None, None, None


class SecurityAgent(BaseAgent):
    """Real security scanner agent with LLM analysis + all-branch support."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'SecurityAgent',
            config={
                **(config or {}),
                'role': 'security analyst',
                'goal': 'Scan repos for real vulnerabilities and explain them',
                'capabilities': [
                    'scan_repo',
                    'scan_all_branches',
                    'analyze_vulnerabilities',
                    'explain_risks',
                ],
                'max_retries': 2,
            }
        )
        self.total_scans = 0
        self.successful_scans = 0
        self.failed_scans = 0

    # ============================================
    # Main Entry Point
    # ============================================
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        sid = context.get('sid') if context else None

        if not isinstance(input_data, dict):
            input_data = {'query': str(input_data)}

        # Extract repo URL
        repo_url = (
            input_data.get('repo_url')
            or input_data.get('repoUrl')
            or input_data.get('query', '')
        )
        branch_override = input_data.get('branch')
        all_branches = bool(input_data.get('all_branches', False))

        # Try extract URL from text
        if repo_url and 'github.com' not in repo_url:
            m = re.search(r'https?://github\.com/\S+', repo_url)
            if m:
                repo_url = m.group(0)

        owner, repo, url_branch = _parse_github_url(repo_url)
        if not owner:
            return self._error_response(
                "Could not parse GitHub URL",
                sid=sid,
                hint="Provide URL like: https://github.com/owner/repo",
            )

        # Priority: explicit > url > default
        branch = branch_override or url_branch

        # Build mode string (avoid f-string backslash issue)
        if all_branches:
            mode_str = 'ALL BRANCHES'
        else:
            mode_str = 'branch=' + (branch or 'default')

        self.emit_log("=" * 60, "info", sid)
        self.emit_log("🛡️  SecurityAgent started", "info", sid)
        self.emit_log(f"   Repo: {owner}/{repo}", "info", sid)
        self.emit_log(f"   Mode: {mode_str}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        start_time = time.time()

        try:
            if all_branches:
                result = self._scan_all_branches(owner, repo, sid, start_time)
            else:
                result = self._scan_single_branch(owner, repo, branch, sid, start_time)

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            self.failed_scans += 1
            self.track_metric(False, elapsed)
            self.emit_log(f"❌ Security scan failed: {str(e)[:200]}", "error", sid)
            import traceback
            traceback.print_exc()
            return self._error_response(str(e), sid=sid)

    # ============================================
    # SINGLE BRANCH SCAN
    # ============================================
    def _scan_single_branch(self, owner, repo, branch, sid, start_time) -> Dict:
        """Scan a single branch (or default)."""

        # Resolve default branch if not given
        if not branch:
            branch = self._get_default_branch(owner, repo, sid)
            self.emit_log(f"   Auto-detected branch: {branch}", "info", sid)

        self.emit_log("🔍 Step 1/3: Running security scanner...", "info", sid)
        scan_result = self._run_scanner(owner, repo, branch, sid)

        if not scan_result.get('success'):
            self.failed_scans += 1
            return self._error_response(scan_result.get('error', 'Scan failed'), sid=sid)

        total = scan_result.get('total', 0)
        critical = scan_result.get('critical', 0)
        high = scan_result.get('high', 0)
        medium = scan_result.get('medium', 0)
        low = scan_result.get('low', 0)
        score = scan_result.get('score', 0)
        issues = scan_result.get('issues', [])

        self.emit_log(
            f"   ✓ Scan complete: {total} issues "
            f"(C:{critical} H:{high} M:{medium} L:{low}) Score: {score}/100",
            "success", sid
        )

        # LLM analysis
        self.emit_log("🧠 Step 2/3: Analyzing findings with LLM...", "info", sid)
        analysis = self._analyze_with_llm(owner, repo, issues, score, sid)

        self.emit_log("📝 Step 3/3: Building report...", "info", sid)

        elapsed = time.time() - start_time
        self.total_scans += 1
        self.successful_scans += 1
        self.track_metric(True, elapsed)

        response_md = self._build_report_md(
            owner=owner, repo=repo, branch=branch,
            total=total, critical=critical, high=high,
            medium=medium, low=low, score=score,
            issues=issues, analysis=analysis, elapsed=elapsed,
        )

        self._emit_chat(sid, response_md)

        self.emit_log("=" * 60, "success", sid)
        self.emit_log(f"✅ Security scan complete in {elapsed:.1f}s", "success", sid)
        self.emit_log("=" * 60, "success", sid)

        return {
            'success': True,
            'type': 'security',
            'status': 'completed',
            'owner': owner, 'repo': repo, 'branch': branch,
            'critical': critical, 'high': high,
            'medium': medium, 'low': low,
            'total': total, 'score': score,
            'issues': issues[:30],
            'analysis': analysis,
            'duration': f'{elapsed:.1f}s',
            'response': response_md,
            'result': {
                'critical': critical, 'high': high,
                'medium': medium, 'low': low,
                'total': total, 'score': score,
                'issues': issues[:30], 'branch': branch,
            },
        }

    # ============================================
    # ⭐ ALL BRANCHES SCAN
    # ============================================
    def _scan_all_branches(self, owner, repo, sid, start_time) -> Dict:
        """Scan ALL branches and produce combined report."""

        # Get list of branches
        self.emit_log("📋 Step 1/4: Fetching branches from GitHub...", "info", sid)
        branches = self._list_branches(owner, repo, sid)

        if not branches:
            return self._error_response(
                f"No branches found for {owner}/{repo}",
                sid=sid,
                hint="Check if repo is public or GITHUB_TOKEN has access",
            )

        self.emit_log(f"   ✓ Found {len(branches)} branches", "success", sid)
        for b in branches[:10]:
            self.emit_log(f"      • {b}", "info", sid)

        # Scan each branch
        self.emit_log("🔍 Step 2/4: Scanning each branch...", "info", sid)

        branch_results = {}
        total_combined = 0
        critical_combined = 0
        high_combined = 0
        medium_combined = 0
        low_combined = 0

        for i, b in enumerate(branches, 1):
            self.emit_log("", "info", sid)
            self.emit_log(f"   [{i}/{len(branches)}] Scanning branch: {b}", "info", sid)

            result = self._run_scanner(owner, repo, b, sid)

            if not result.get('success'):
                self.emit_log(
                    f"      ❌ Failed: {result.get('error', 'unknown')[:100]}",
                    "error", sid
                )
                branch_results[b] = {'error': result.get('error', 'unknown')}
                continue

            branch_results[b] = result
            total_combined += result.get('total', 0)
            critical_combined += result.get('critical', 0)
            high_combined += result.get('high', 0)
            medium_combined += result.get('medium', 0)
            low_combined += result.get('low', 0)

            self.emit_log(
                f"      ✓ {b}: {result.get('total', 0)} issues "
                f"(C:{result.get('critical', 0)} H:{result.get('high', 0)})",
                "success", sid
            )

        # Combined score (average)
        scores = [r.get('score', 100) for r in branch_results.values() if 'score' in r]
        avg_score = round(sum(scores) / len(scores)) if scores else 0

        # LLM analysis on combined issues
        self.emit_log("", "info", sid)
        self.emit_log("🧠 Step 3/4: Analyzing combined findings with LLM...", "info", sid)

        # Merge top issues
        all_issues = []
        for b, r in branch_results.items():
            if 'issues' in r:
                for iss in r['issues'][:5]:  # top 5 per branch
                    iss_copy = dict(iss)
                    iss_copy['branch'] = b
                    all_issues.append(iss_copy)

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_issues.sort(key=lambda i: severity_order.get(i.get('severity', 'low'), 4))
        top_issues = all_issues[:20]

        analysis = self._analyze_with_llm(
            owner, repo, top_issues, avg_score, sid,
            multi_branch=True, branch_count=len(branches),
        )

        self.emit_log("📝 Step 4/4: Building combined report...", "info", sid)

        elapsed = time.time() - start_time
        self.total_scans += 1
        self.successful_scans += 1
        self.track_metric(True, elapsed)

        response_md = self._build_all_branches_report_md(
            owner=owner, repo=repo,
            branches=branches,
            branch_results=branch_results,
            total=total_combined,
            critical=critical_combined,
            high=high_combined,
            medium=medium_combined,
            low=low_combined,
            avg_score=avg_score,
            analysis=analysis,
            elapsed=elapsed,
        )

        self._emit_chat(sid, response_md)

        self.emit_log("=" * 60, "success", sid)
        self.emit_log(
            f"✅ All-branch scan complete: {len(branches)} branches, "
            f"{total_combined} total issues in {elapsed:.1f}s",
            "success", sid
        )
        self.emit_log("=" * 60, "success", sid)

        return {
            'success': True,
            'type': 'security_all_branches',
            'status': 'completed',
            'owner': owner, 'repo': repo,
            'branches': branches,
            'branch_count': len(branches),
            'branch_results': {
                k: {
                    'total': v.get('total', 0),
                    'critical': v.get('critical', 0),
                    'high': v.get('high', 0),
                    'medium': v.get('medium', 0),
                    'low': v.get('low', 0),
                    'score': v.get('score', 0),
                    'error': v.get('error'),
                }
                for k, v in branch_results.items()
            },
            'critical': critical_combined,
            'high': high_combined,
            'medium': medium_combined,
            'low': low_combined,
            'total': total_combined,
            'score': avg_score,
            'issues': top_issues,
            'analysis': analysis,
            'duration': f'{elapsed:.1f}s',
            'response': response_md,
            'result': {
                'critical': critical_combined,
                'high': high_combined,
                'medium': medium_combined,
                'low': low_combined,
                'total': total_combined,
                'score': avg_score,
                'issues': top_issues,
                'branches': branches,
                'branch_count': len(branches),
            },
        }

    # ============================================
    # List branches
    # ============================================
    def _list_branches(self, owner: str, repo: str, sid) -> List[str]:
        """Get list of all branches."""
        token = os.getenv('GITHUB_TOKEN')
        headers = {'Accept': 'application/vnd.github+json'}
        if token:
            headers['Authorization'] = f'token {token}'

        try:
            r = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/branches?per_page=100',
                headers=headers, timeout=15,
            )
            if r.status_code == 200:
                return [b['name'] for b in r.json()]
            else:
                self.emit_log(
                    f"   ⚠ GitHub API error {r.status_code}",
                    "warning", sid
                )
        except Exception as e:
            self.emit_log(f"   ⚠ Branch list failed: {str(e)[:100]}", "warning", sid)
        return []

    def _get_default_branch(self, owner: str, repo: str, sid) -> str:
        """Get default branch."""
        token = os.getenv('GITHUB_TOKEN')
        headers = {'Accept': 'application/vnd.github+json'}
        if token:
            headers['Authorization'] = f'token {token}'

        try:
            r = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers, timeout=10,
            )
            if r.status_code == 200:
                return r.json().get('default_branch', 'main')
        except Exception:
            pass
        return 'main'

    # ============================================
    # Run scanner (tool)
    # ============================================
    def _run_scanner(self, owner: str, repo: str, branch: str, sid) -> Dict:
        try:
            self.emit_log("   🔄 Importing security_scanner...", "info", sid)
            from services.security_scanner import security_scanner
            self.emit_log("   ✓ security_scanner imported", "success", sid)

            self.emit_log(f"   📥 Cloning {owner}/{repo} @ {branch}...", "info", sid)
            clone = security_scanner.clone_repo(owner, repo, branch=branch)
            if not clone.get('success'):
                err = clone.get('error', 'Clone failed')
                self.emit_log(f"   ❌ Clone failed: {err}", "error", sid)
                return {'success': False, 'error': err}

            repo_path = clone['path']
            self.emit_log("   ✓ Cloned", "success", sid)

            try:
                self.emit_log("   🔎 Scanning for vulnerabilities...", "info", sid)
                scan = security_scanner.scan(repo_path)
                self.emit_log(
                    f"   ✓ Scan done: {scan.get('total', 0)} issues",
                    "success", sid
                )
                return scan
            finally:
                security_scanner.cleanup(repo_path)
        except ImportError as e:
            err = f'security_scanner import failed: {e}'
            self.emit_log(f"   ❌ {err}", "error", sid)
            print(f"[SECURITY] {err}", flush=True)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': err}
        except Exception as e:
            err = f'{type(e).__name__}: {str(e)[:300]}'
            self.emit_log(f"   ❌ Scanner error: {err}", "error", sid)
            print(f"[SECURITY] {err}", flush=True)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': err}

    # ============================================
    # LLM Analysis
    # ============================================
    def _analyze_with_llm(
        self,
        owner: str,
        repo: str,
        issues: List[Dict],
        score: int,
        sid,
        multi_branch: bool = False,
        branch_count: int = 1,
    ) -> str:
        if not issues:
            return "No security issues found. The codebase looks clean."

        groq_key = os.getenv('GROQ_API_KEY')
        if not groq_key:
            self.emit_log("   ⚠ GROQ_API_KEY not set — skipping LLM analysis", "warning", sid)
            return ""

        top_issues = issues[:15]
        issues_lines = []
        for i in top_issues:
            line = (
                f"- [{i.get('severity', '?').upper()}] "
                f"{i.get('type', '?')} "
                f"in {i.get('file', '?')}:{i.get('line', '?')}"
            )
            if i.get('branch'):
                line += f" (branch: {i['branch']})"
            line += f" — {i.get('message', '')}"
            issues_lines.append(line)
        issues_text = "\n".join(issues_lines)

        if multi_branch:
            context_str = f"across {branch_count} branches"
        else:
            context_str = "on the default branch"

        prompt = (
            f"You are a senior security analyst reviewing {owner}/{repo} {context_str}.\n"
            f"Average security score: {score}/100\n\n"
            f"Top findings:\n{issues_text}\n\n"
            f"Provide a brief executive summary:\n"
            f"1. **Overall risk level** (Critical/High/Medium/Low)\n"
            f"2. **Top 3 most urgent issues**\n"
            f"3. **Immediate action items** (3-5 bullets)\n\n"
            f"Be concise. Use markdown."
        )

        try:
            model = _get_groq_model()
            self.emit_log(f"   🧠 Calling Groq ({model})...", "info", sid)
            r = requests.post(
                GROQ_API_URL,
                headers={
                    'Authorization': f'Bearer {groq_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.2,
                    'max_tokens': 1500,
                },
                timeout=60,
            )
            if r.status_code != 200:
                self.emit_log(f"   ⚠ LLM error {r.status_code}", "warning", sid)
                return ""
            analysis = r.json()['choices'][0]['message']['content'].strip()
            self.emit_log(f"   ✓ LLM analysis complete ({len(analysis)} chars)", "success", sid)
            return analysis
        except Exception as e:
            self.emit_log(f"   ⚠ LLM analysis failed: {str(e)[:150]}", "warning", sid)
            return ""

    # ============================================
    # Build single-branch report
    # ============================================
    def _build_report_md(self, owner, repo, branch, total, critical, high,
                         medium, low, score, issues, analysis, elapsed) -> str:
        parts = ["## 🛡️ Security Scan Report", ""]
        parts.append(f"**Repo:** `{owner}/{repo}`")
        parts.append(f"**Branch:** `{branch}`")
        parts.append(f"**Scan time:** {elapsed:.1f}s")
        parts.append("")

        if score >= 90:
            badge = "🟢 Excellent"
        elif score >= 70:
            badge = "🟡 Good"
        elif score >= 50:
            badge = "🟠 Needs Attention"
        else:
            badge = "🔴 Critical"

        parts.append(f"### Security Score: **{score}/100** — {badge}")
        parts.append("")
        parts.append("### 📊 Summary")
        parts.append(f"- 🔴 **Critical:** {critical}")
        parts.append(f"- 🟠 **High:** {high}")
        parts.append(f"- 🟡 **Medium:** {medium}")
        parts.append(f"- 🟢 **Low:** {low}")
        parts.append(f"- **Total:** {total}")
        parts.append("")

        if analysis:
            parts.append("### 🧠 AI Analysis")
            parts.append(analysis)
            parts.append("")

        if issues:
            parts.append("### 🚨 Top Findings")
            for i, issue in enumerate(issues[:10], 1):
                sev = issue.get('severity', 'low').upper()
                emoji = {
                    'CRITICAL': '🔴', 'HIGH': '🟠',
                    'MEDIUM': '🟡', 'LOW': '🟢',
                }.get(sev, '•')
                parts.append(f"{i}. {emoji} **{sev}** — {issue.get('message', '')}")
                parts.append(f"   - 📁 `{issue.get('file', '')}:{issue.get('line', '')}`")
            parts.append("")

        if total == 0:
            parts.append("### ✅ No vulnerabilities found!")
        else:
            parts.append(f"*Found **{total}** issues. Review critical & high first.*")

        parts.append("")
        parts.append("*Scanned by SecurityAgent*")
        return '\n'.join(parts)

    # ============================================
    # Build all-branches report
    # ============================================
    def _build_all_branches_report_md(
        self, owner, repo, branches, branch_results,
        total, critical, high, medium, low, avg_score,
        analysis, elapsed,
    ) -> str:
        parts = ["## 🛡️ Security Scan Report — ALL BRANCHES", ""]
        parts.append(f"**Repo:** `{owner}/{repo}`")
        parts.append(f"**Branches scanned:** {len(branches)}")
        parts.append(f"**Scan time:** {elapsed:.1f}s")
        parts.append("")

        if avg_score >= 90:
            badge = "🟢 Excellent"
        elif avg_score >= 70:
            badge = "🟡 Good"
        elif avg_score >= 50:
            badge = "🟠 Needs Attention"
        else:
            badge = "🔴 Critical"

        parts.append(f"### Average Score: **{avg_score}/100** — {badge}")
        parts.append("")

        parts.append("### 📊 Combined Summary")
        parts.append(f"- 🔴 **Critical:** {critical}")
        parts.append(f"- 🟠 **High:** {high}")
        parts.append(f"- 🟡 **Medium:** {medium}")
        parts.append(f"- 🟢 **Low:** {low}")
        parts.append(f"- **Total:** {total}")
        parts.append("")

        # Per-branch breakdown
        parts.append("### 🌿 Per-Branch Breakdown")
        parts.append("")
        parts.append("| Branch | Critical | High | Medium | Low | Total | Score |")
        parts.append("|--------|----------|------|--------|-----|-------|-------|")
        for b in branches:
            r = branch_results.get(b, {})
            if 'error' in r:
                parts.append(f"| `{b}` | ⚠️ error | - | - | - | - | - |")
            else:
                parts.append(
                    f"| `{b}` | {r.get('critical', 0)} | {r.get('high', 0)} | "
                    f"{r.get('medium', 0)} | {r.get('low', 0)} | "
                    f"{r.get('total', 0)} | {r.get('score', 0)}/100 |"
                )
        parts.append("")

        if analysis:
            parts.append("### 🧠 AI Analysis")
            parts.append(analysis)
            parts.append("")

        if total == 0:
            parts.append("### ✅ No vulnerabilities found in any branch!")
        else:
            parts.append(
                f"*Found **{total}** total issues across {len(branches)} branches. "
                f"Review critical & high first.*"
            )

        parts.append("")
        parts.append("*Scanned by SecurityAgent (all-branches mode)*")
        return '\n'.join(parts)

    # ============================================
    # Emit chat + socket events
    # ============================================
    def _emit_chat(self, sid: Optional[str], markdown: str):
        """Emit chat-friendly message to frontend."""
        try:
            from core.event_bus import emit_event, _socketio
            emit_event('security:report', {'markdown': markdown, 'sid': sid})
            if _socketio:
                payload = {
                    'message': markdown,
                    'source': 'SecurityAgent',
                    'type': 'security_report',
                    'timestamp': time.strftime('%H:%M:%S'),
                }
                if sid:
                    _socketio.emit('chat_response', payload, room=sid)
                else:
                    _socketio.emit('chat_response', payload)
        except Exception:
            pass

    # ============================================
    # Error response
    # ============================================
    def _error_response(self, msg, sid=None, hint=''):
        print(f"[SECURITY] ERROR: {msg}", flush=True)
        self.emit_log(f"❌ Error: {msg}", "error", sid)
        parts = ["## ❌ Security Scan Failed", "", f"**Error:** {msg}"]
        if hint:
            parts.append("")
            parts.append(f"**Hint:** {hint}")
        response = '\n'.join(parts)
        self._emit_chat(sid, response)
        return {'success': False, 'error': msg, 'response': response}

    # ============================================
    # Metrics
    # ============================================
    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {
            **base,
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'success_rate': (
                (self.successful_scans / self.total_scans * 100)
                if self.total_scans > 0 else 0
            ),
        }