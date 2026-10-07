"""
RepoScanner — Multi-language error detection
=============================================
Scans a repository for:
- Python syntax errors (via ast)
- JavaScript / TypeScript lint issues (regex-based)
- Unused imports
- Common bug patterns
- TODO/FIXME markers
- Debug prints left behind

Works without external linters (pyflakes, eslint).
"""

import os
import re
import ast
import json
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional


# ──────────────────────────────────────────────
# Language detection by extension
# ──────────────────────────────────────────────
LANG_BY_EXT = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.rb': 'ruby',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.yml': 'yaml',
    '.yaml': 'yaml',
}

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'env', 'build', 'dist', '.next', 'coverage', '.pytest_cache',
    'vendor', 'target', 'bin', 'obj', '.idea', '.vscode',
}

# Files to skip
SKIP_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', '.DS_Store',
}

# Max file size to scan (bytes)
MAX_FILE_SIZE = 500_000  # 500KB


class RepoScanner:
    """Scans repos for errors across multiple languages."""

    def __init__(self):
        self.temp_root = os.path.join(tempfile.gettempdir(), 'repo_scans')
        os.makedirs(self.temp_root, exist_ok=True)

    # ──────────────────────────────────────────
    # Clone
    # ──────────────────────────────────────────
    def clone_repo(self, owner: str, repo: str, branch: str = 'main') -> Dict:
        """Clone repo at given branch."""
        scan_id = f"{owner}-{repo}-{int(os.getpid())}"
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

    # ──────────────────────────────────────────
    # Main scan
    # ──────────────────────────────────────────
    def scan(self, repo_path: str) -> Dict:
        """Scan entire repo for issues."""
        all_issues: List[Dict] = []
        lang_counts: Dict[str, int] = {}
        files_scanned = 0
        files_skipped = 0

        for root, dirs, files in os.walk(repo_path):
            # Skip unwanted dirs
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                if filename in SKIP_FILES:
                    files_skipped += 1
                    continue

                ext = os.path.splitext(filename)[1].lower()
                lang = LANG_BY_EXT.get(ext)
                if not lang:
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
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1

                    # Scan based on language
                    if lang == 'python':
                        issues = self._scan_python(content, relpath)
                    elif lang in ('javascript', 'typescript'):
                        issues = self._scan_js_ts(content, relpath, lang)
                    elif lang == 'json':
                        issues = self._scan_json(content, relpath)
                    elif lang == 'yaml':
                        issues = self._scan_yaml(content, relpath)
                    else:
                        issues = self._scan_generic(content, relpath, lang)

                    all_issues.extend(issues)
                except Exception as e:
                    all_issues.append({
                        'file': relpath,
                        'line': 0,
                        'type': 'scan_error',
                        'severity': 'info',
                        'message': f'Scan failed: {str(e)[:100]}',
                    })

        # Sort by severity
        severity_order = {'error': 0, 'warning': 1, 'info': 2}
        all_issues.sort(key=lambda i: severity_order.get(i.get('severity', 'info'), 3))

        critical = sum(1 for i in all_issues if i.get('severity') == 'error')
        warnings = sum(1 for i in all_issues if i.get('severity') == 'warning')
        infos = sum(1 for i in all_issues if i.get('severity') == 'info')

        # Detect primary language
        primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else 'unknown'

        return {
            'success': True,
            'total_issues': len(all_issues),
            'critical': critical,
            'warnings': warnings,
            'info': infos,
            'language': primary_lang,
            'languages': lang_counts,
            'files_scanned': files_scanned,
            'files_skipped': files_skipped,
            'issues': all_issues[:200],  # cap at 200
        }

    # ──────────────────────────────────────────
    # Python scanner
    # ──────────────────────────────────────────
    def _scan_python(self, content: str, relpath: str) -> List[Dict]:
        issues: List[Dict] = []

        # 1. Syntax errors via ast
        try:
            tree = ast.parse(content, filename=relpath)
        except SyntaxError as e:
            issues.append({
                'file': relpath,
                'line': e.lineno or 0,
                'col': e.offset or 0,
                'type': 'syntax',
                'severity': 'error',
                'message': f"SyntaxError: {e.msg}",
                'code': (e.text or '').strip(),
            })
            return issues  # can't continue without parsing

        lines = content.split('\n')

        # 2. Unused imports
        issues.extend(self._check_unused_imports(tree, content, lines, relpath))

        # 3. Bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        'file': relpath,
                        'line': node.lineno,
                        'type': 'style',
                        'severity': 'warning',
                        'message': "Bare 'except:' — should catch specific exceptions",
                    })

        # 4. Mutable default args
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            'file': relpath,
                            'line': node.lineno,
                            'type': 'bug',
                            'severity': 'warning',
                            'message': f"Mutable default argument in '{node.name}' — use None instead",
                        })

        # 5. Debug prints left in (info level)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r'^print\s*\(', stripped) and 'debug' in stripped.lower():
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'style',
                    'severity': 'info',
                    'message': 'Debug print statement found',
                })

        # 6. TODO / FIXME
        for i, line in enumerate(lines, 1):
            m = re.search(r'#\s*(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE)
            if m:
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'todo',
                    'severity': 'info',
                    'message': f"{m.group(1).upper()} marker",
                })

        # 7. `== None` / `!= None` (should use `is None`)
        for i, line in enumerate(lines, 1):
            if re.search(r'[!=]=\s*None\b', line) or re.search(r'\bNone\s*[!=]=', line):
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'style',
                    'severity': 'info',
                    'message': "Use 'is None' / 'is not None' instead of == / !=",
                })

        return issues

    def _check_unused_imports(self, tree, content, lines, relpath) -> List[Dict]:
        """Detect unused imports."""
        issues: List[Dict] = []
        imported_names = {}  # name -> lineno

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imported_names[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    name = alias.asname or alias.name
                    imported_names[name] = node.lineno

        # Count usage (skip import lines themselves)
        used = set()
        for name, lineno in imported_names.items():
            pattern = re.compile(r'\b' + re.escape(name) + r'\b')
            for i, line in enumerate(lines, 1):
                if i == lineno:
                    continue
                if pattern.search(line):
                    used.add(name)
                    break

        for name, lineno in imported_names.items():
            if name not in used:
                issues.append({
                    'file': relpath,
                    'line': lineno,
                    'type': 'unused_import',
                    'severity': 'warning',
                    'message': f"Unused import: '{name}'",
                })

        return issues

    # ──────────────────────────────────────────
    # JS/TS scanner
    # ──────────────────────────────────────────
    def _scan_js_ts(self, content: str, relpath: str, lang: str) -> List[Dict]:
        issues: List[Dict] = []
        lines = content.split('\n')

        # 1. Debug statements
        for i, line in enumerate(lines, 1):
            if re.search(r'\bconsole\.(log|debug|warn)\s*\(', line):
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'style',
                    'severity': 'info',
                    'message': 'console.log/debug/warn left in code',
                })

        # 2. `==` instead of `===`
        for i, line in enumerate(lines, 1):
            if '//' in line:
                line = line.split('//')[0]
            if re.search(r'[^=!<>]==[^=]', line) or re.search(r'!=[^=]', line):
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'style',
                    'severity': 'warning',
                    'message': "Use '===' or '!==' instead of '==' / '!='",
                })

        # 3. Unused imports (basic)
        imported = re.findall(r'import\s+(\w+)', content)
        for name in set(imported):
            usage = re.findall(r'\b' + re.escape(name) + r'\b', content)
            if len(usage) <= 1:
                issues.append({
                    'file': relpath,
                    'line': 1,
                    'type': 'unused_import',
                    'severity': 'warning',
                    'message': f"Unused import: '{name}'",
                })

        # 4. TODO markers
        for i, line in enumerate(lines, 1):
            if re.search(r'//\s*(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE):
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'todo',
                    'severity': 'info',
                    'message': 'TODO/FIXME marker',
                })

        # 5. Syntax quick-check (unbalanced braces)
        open_braces = content.count('{') - content.count('}')
        open_parens = content.count('(') - content.count(')')
        if open_braces != 0:
            issues.append({
                'file': relpath,
                'line': 0,
                'type': 'syntax',
                'severity': 'error',
                'message': f"Unbalanced curly braces: {open_braces:+d}",
            })
        if open_parens != 0:
            issues.append({
                'file': relpath,
                'line': 0,
                'type': 'syntax',
                'severity': 'error',
                'message': f"Unbalanced parentheses: {open_parens:+d}",
            })

        return issues

    # ──────────────────────────────────────────
    # JSON scanner
    # ──────────────────────────────────────────
    def _scan_json(self, content: str, relpath: str) -> List[Dict]:
        try:
            json.loads(content)
            return []
        except json.JSONDecodeError as e:
            return [{
                'file': relpath,
                'line': e.lineno,
                'col': e.colno,
                'type': 'syntax',
                'severity': 'error',
                'message': f"Invalid JSON: {e.msg}",
            }]

    # ──────────────────────────────────────────
    # YAML scanner (basic)
    # ──────────────────────────────────────────
    def _scan_yaml(self, content: str, relpath: str) -> List[Dict]:
        issues: List[Dict] = []
        # Basic tab detection (YAML forbids tabs)
        for i, line in enumerate(content.split('\n'), 1):
            if '\t' in line:
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'syntax',
                    'severity': 'error',
                    'message': 'Tabs are not allowed in YAML — use spaces',
                })
        return issues

    # ──────────────────────────────────────────
    # Generic scanner
    # ──────────────────────────────────────────
    def _scan_generic(self, content: str, relpath: str, lang: str) -> List[Dict]:
        issues: List[Dict] = []
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'(TODO|FIXME|XXX|HACK)\b', line, re.IGNORECASE):
                issues.append({
                    'file': relpath,
                    'line': i,
                    'type': 'todo',
                    'severity': 'info',
                    'message': 'TODO/FIXME marker',
                })
        return issues


repo_scanner = RepoScanner()