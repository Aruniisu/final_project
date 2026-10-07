"""
SecurityScanner — Real Security Vulnerability Detection
========================================================
Detects:
- Hardcoded secrets (API keys, passwords, tokens)
- Private keys
- SQL injection patterns
- XSS vulnerabilities
- Weak cryptography
- Debug mode enabled
- CORS wildcards
- Eval/exec usage
- HTTP (not HTTPS) URLs
- Exposed .env files
- Insecure random
- Command injection
"""

import os
import re
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional


SCAN_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.rs',
    '.json', '.yaml', '.yml', '.env', '.txt', '.md',
    '.html', '.htm', '.xml', '.sh', '.bash', '.ps1', '.sql',
}

SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'env', 'build', 'dist', '.next', 'coverage', '.pytest_cache',
    'vendor', 'target', 'bin', 'obj', '.idea', '.vscode',
    '.terraform', 'migrations',
}

OK_SECRET_FILES = {'.env.example', '.env.sample', '.env.template'}
MAX_FILE_SIZE = 1_000_000


PATTERNS = [
    # ── CRITICAL: Hardcoded secrets ──
    {
        'regex': r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\'"]((?!your[_-]?|xxx|placeholder|example|changeme|dummy|test[_-]?|fake[_-]?|<)[A-Za-z0-9_\-]{20,})[\'"]',
        'severity': 'critical',
        'type': 'hardcoded_secret',
        'message': 'Hardcoded API key/secret detected',
    },
    {
        'regex': r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"]((?!your[_-]?|xxx|placeholder|example|changeme|dummy|test[_-]?|fake[_-]?|<)[^\'"\s]{8,})[\'"]',
        'severity': 'critical',
        'type': 'hardcoded_password',
        'message': 'Hardcoded password detected',
    },
    {
        'regex': r'ghp_[A-Za-z0-9]{36}',
        'severity': 'critical',
        'type': 'github_token',
        'message': 'GitHub personal access token detected',
    },
    {
        'regex': r'gsk_[A-Za-z0-9]{40,}',
        'severity': 'critical',
        'type': 'groq_api_key',
        'message': 'Groq API key detected',
    },
    {
        'regex': r'sk-[A-Za-z0-9]{32,}',
        'severity': 'critical',
        'type': 'openai_api_key',
        'message': 'OpenAI API key detected',
    },
    {
        'regex': r'AKIA[0-9A-Z]{16}',
        'severity': 'critical',
        'type': 'aws_access_key',
        'message': 'AWS access key detected',
    },
    {
        'regex': r'AIza[0-9A-Za-z\-_]{35}',
        'severity': 'critical',
        'type': 'google_api_key',
        'message': 'Google API key detected',
    },
    {
        'regex': r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)?\s*PRIVATE KEY-----',
        'severity': 'critical',
        'type': 'private_key',
        'message': 'Private key found in source code',
    },

    # ── HIGH: Injection vulnerabilities ──
    {
        'regex': r'(?i)(cursor\.execute|execute|query)\s*\(\s*f[\'"]',
        'severity': 'high',
        'type': 'sql_injection',
        'message': 'SQL query with f-string — possible SQL injection',
    },
    {
        'regex': r'(?i)(cursor\.execute|execute)\s*\([^,)]*%[^,)]*\)',
        'severity': 'high',
        'type': 'sql_injection',
        'message': 'SQL query with % formatting — possible SQL injection',
    },
    {
        'regex': r'(?i)(cursor\.execute|execute)\s*\([^,)]*\.format\s*\(',
        'severity': 'high',
        'type': 'sql_injection',
        'message': 'SQL query with .format() — possible SQL injection',
    },
    {
        'regex': r'\.innerHTML\s*=\s*(?![\'"])',
        'severity': 'high',
        'type': 'xss',
        'message': 'innerHTML with variable — possible XSS',
    },
    {
        'regex': r'dangerouslySetInnerHTML\s*=\s*\{\{',
        'severity': 'high',
        'type': 'xss',
        'message': 'React dangerouslySetInnerHTML — check for XSS',
    },
    {
        'regex': r'(?i)\beval\s*\([^)]*\)',
        'severity': 'high',
        'type': 'eval_usage',
        'message': 'eval() usage — code injection risk',
    },
    {
        'regex': r'(?i)\bexec\s*\(\s*(?![\'"])',
        'severity': 'high',
        'type': 'exec_usage',
        'message': 'exec() with variable — code injection risk',
    },
    {
        'regex': r'(?i)subprocess\.(call|run|Popen|check_output)\s*\([^)]*shell\s*=\s*True',
        'severity': 'high',
        'type': 'shell_injection',
        'message': 'subprocess with shell=True — command injection risk',
    },
    {
        'regex': r'(?i)os\.system\s*\(',
        'severity': 'high',
        'type': 'os_system',
        'message': 'os.system() — command injection risk',
    },
    {
        'regex': r'(?i)pickle\.loads?\s*\(',
        'severity': 'high',
        'type': 'insecure_deserialization',
        'message': 'pickle.load — insecure deserialization',
    },

    # ── MEDIUM: Weak crypto/config ──
    {
        'regex': r'(?i)hashlib\.(md5|sha1)\s*\(',
        'severity': 'medium',
        'type': 'weak_crypto',
        'message': 'Weak hash algorithm (md5/sha1) — use sha256+',
    },
    {
        'regex': r'(?i)debug\s*=\s*True',
        'severity': 'medium',
        'type': 'debug_mode',
        'message': 'Debug mode enabled — disable in production',
    },
    {
        'regex': r'(?i)CORS\s*\([^)]*origins\s*=\s*[\'"]\*[\'"]',
        'severity': 'medium',
        'type': 'cors_wildcard',
        'message': 'CORS allows all origins',
    },
    {
        'regex': r'(?i)cors_allowed_origins\s*=\s*[\'"]\*[\'"]',
        'severity': 'medium',
        'type': 'cors_wildcard',
        'message': 'CORS wildcard allowed',
    },
    {
        'regex': r'(?i)verify\s*=\s*False',
        'severity': 'medium',
        'type': 'ssl_verify_disabled',
        'message': 'SSL verification disabled',
    },
    {
        'regex': r'(?i)\brandom\.random\s*\(|\brandom\.randint\s*\(',
        'severity': 'medium',
        'type': 'insecure_random',
        'message': 'random module — use secrets for security',
    },

    # ── LOW: Best practices ──
    {
        'regex': r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|schemas?\.|www\.w3\.org)[a-zA-Z0-9\-\.]+',
        'severity': 'low',
        'type': 'insecure_http',
        'message': 'HTTP (not HTTPS) URL',
    },
    {
        'regex': r'(?i)except\s*:\s*pass',
        'severity': 'low',
        'type': 'silent_exception',
        'message': 'Silent exception — may hide errors',
    },
]


class SecurityScanner:
    """Real security vulnerability scanner."""

    def __init__(self):
        self.temp_root = os.path.join(tempfile.gettempdir(), 'security_scans')
        os.makedirs(self.temp_root, exist_ok=True)

    def clone_repo(self, owner: str, repo: str, branch: str = 'main') -> Dict:
        """Clone repo at given branch."""
        scan_id = f"{owner}-{repo}-{int(os.getpid())}-{int(__import__('time').time())}"
        target = os.path.join(self.temp_root, scan_id)

        if os.path.exists(target):
            shutil.rmtree(target, ignore_errors=True)

        token = os.getenv('GITHUB_TOKEN')
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
                }
            return {'success': True, 'path': target, 'branch': branch}
        except Exception as e:
            return {'success': False, 'error': str(e)[:300]}

    def cleanup(self, path: str):
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    def scan(self, repo_path: str) -> Dict:
        """Scan repo for REAL security vulnerabilities."""
        all_issues: List[Dict] = []
        files_scanned = 0
        files_skipped = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                if filename in OK_SECRET_FILES:
                    files_skipped += 1
                    continue

                ext = os.path.splitext(filename)[1].lower()
                is_dotenv = filename.startswith('.env')
                if not is_dotenv and ext not in SCAN_EXTENSIONS:
                    continue

                filepath = os.path.join(root, filename)
                relpath = os.path.relpath(filepath, repo_path)

                try:
                    size = os.path.getsize(filepath)
                    if size > MAX_FILE_SIZE:
                        files_skipped += 1
                        continue

                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    files_scanned += 1

                    # Special: .env committed
                    if is_dotenv and not filename.endswith('.example'):
                        real_secrets = self._check_dotenv(content)
                        if real_secrets:
                            all_issues.append({
                                'file': relpath,
                                'line': 1,
                                'type': 'env_committed',
                                'severity': 'critical',
                                'message': f'.env committed with {len(real_secrets)} real secret(s)',
                                'code': ', '.join(real_secrets[:3]),
                            })

                    # Run regex patterns
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if stripped.startswith('#') or stripped.startswith('//'):
                            continue

                        for pattern in PATTERNS:
                            try:
                                if re.search(pattern['regex'], line):
                                    if self._is_false_positive(line, pattern['type']):
                                        continue
                                    all_issues.append({
                                        'file': relpath,
                                        'line': i,
                                        'type': pattern['type'],
                                        'severity': pattern['severity'],
                                        'message': pattern['message'],
                                        'code': line.strip()[:200],
                                    })
                            except re.error:
                                continue
                except Exception:
                    pass

        # Deduplicate
        seen = set()
        unique_issues = []
        for issue in all_issues:
            key = (issue['file'], issue['line'], issue['type'])
            if key in seen:
                continue
            seen.add(key)
            unique_issues.append(issue)

        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        unique_issues.sort(key=lambda i: severity_order.get(i.get('severity', 'low'), 4))

        critical = sum(1 for i in unique_issues if i['severity'] == 'critical')
        high = sum(1 for i in unique_issues if i['severity'] == 'high')
        medium = sum(1 for i in unique_issues if i['severity'] == 'medium')
        low = sum(1 for i in unique_issues if i['severity'] == 'low')

        # Score
        score = 100
        score -= critical * 20
        score -= high * 8
        score -= medium * 3
        score -= low * 1
        score = max(0, min(100, score))

        return {
            'success': True,
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
            'total': len(unique_issues),
            'score': score,
            'files_scanned': files_scanned,
            'files_skipped': files_skipped,
            'issues': unique_issues[:100],
        }

    def _check_dotenv(self, content: str) -> List[str]:
        """Return list of variable names with real secrets."""
        real_secrets = []
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('\'"')

            if not value:
                continue
            if any(p in value.lower() for p in ['your_', 'xxx', 'placeholder', 'changeme', 'example', '<', 'dummy', 'test_']):
                continue
            if len(value) < 8:
                continue
            if value.lower() in ('true', 'false', 'localhost', 'development', 'production'):
                continue

            real_secrets.append(key)
        return real_secrets

    def _is_false_positive(self, line: str, pattern_type: str) -> bool:
        """Filter common false positives."""
        line_lower = line.lower().strip()

        if line_lower.startswith('#') or line_lower.startswith('//') or line_lower.startswith('*'):
            return True

        if pattern_type in ('hardcoded_secret', 'hardcoded_password', 'hardcoded_secret_key'):
            if 'getenv' in line_lower or 'process.env' in line_lower or 'os.environ' in line_lower:
                return True

        if any(x in line_lower for x in ['your_', 'xxx', 'placeholder', 'changeme', 'example', 'dummy', '<your']):
            return True

        return False


# Global instance
security_scanner = SecurityScanner()