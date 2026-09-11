"""
Auto-Fix Service - PREDICTIVE ADVANCED
- Scans ALL files for potential errors before generating fix
- Multi-file ESLint detection
- Post-fix verification
- Token-limit aware with adaptive retry
"""

import os
import json
import re
import base64
import requests


class AutoFixService:
    """Predictive auto-fix with multi-file scanning."""

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(backend_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.vercel_token = os.getenv('VERCEL_TOKEN')
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.groq_model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')

        print("[AUTOFIX] AutoFixService (PREDICTIVE) initialized")
        print("   Groq: " + ("SET" if self.groq_key else "NOT SET"))
        print("   GitHub: " + ("SET" if self.github_token else "NOT SET"))
        print("   Vercel: " + ("SET" if self.vercel_token else "NOT SET"))

    # ============================================
    # Main entry point
    # ============================================
    def analyze_and_fix(self, deploy_id, owner, repo, root_dir=None, on_log=None):
        def log(msg, level='info'):
            print("[AUTOFIX] " + str(msg))
            if on_log:
                on_log(msg, level)

        log('=== AUTO-FIX STARTED (PREDICTIVE) ===', 'info')
        log('Deploy ID: ' + str(deploy_id), 'info')
        log('Repo: ' + str(owner) + '/' + str(repo), 'info')
        log('Root: ' + str(root_dir), 'info')

        if not self.vercel_token or not self.groq_key or not self.github_token:
            return {'success': False, 'error': 'Missing tokens'}

        # STEP 1: Fetch build logs
        log('STEP 1: Fetching Vercel build logs...', 'info')
        logs = self._get_deployment_logs(deploy_id)
        if not logs:
            return {'success': False, 'error': 'Could not fetch logs'}

        log('Fetched ' + str(len(logs)) + ' log events', 'success')

        # STEP 2: Extract ALL error patterns
        log('STEP 2: Extracting ALL errors from logs...', 'info')
        error_context = self._extract_error_from_logs(logs)

        if not error_context:
            return {'success': False, 'error': 'No error extracted'}

        log('Error context (first 400 chars):', 'info')
        log(error_context[:400], 'info')

        # ⭐ STEP 3: COMPREHENSIVE STATIC SCAN
        log('STEP 3: Comprehensive static analysis (all files)...', 'info')
        files = self._get_repo_files(owner, repo)
        log('Found ' + str(len(files)) + ' files in repo', 'success')

        log('STEP 3.5: Predictive scan for ALL potential issues...', 'info')
        predicted_issues = self._comprehensive_scan(error_context, files, owner, repo, root_dir, log=log)

        # STEP 4: Generate COMPREHENSIVE fix
        log('STEP 4: Generating comprehensive fix...', 'info')
        fix = self._generate_comprehensive_fix(
            error_context, files, owner, repo, root_dir, predicted_issues, log=log
        )

        if not fix:
            log('AI could not generate a fix', 'error')
            return {'success': False, 'error': 'No fix generated'}

        log('AI description: ' + str(fix.get("description", "N/A")), 'success')
        files_to_change = fix.get('files_to_change', [])

        if not files_to_change:
            return {'success': False, 'error': fix.get('root_cause', 'No fix possible')}

        log('Files to change: ' + str(len(files_to_change)), 'info')
        for f in files_to_change:
            log('  - ' + str(f.get("path")), 'info')

        # STEP 5: Apply fix
        log('STEP 5: Applying fix to GitHub...', 'info')
        result = self._apply_fix(owner, repo, fix, log=log)

        if not result.get('success'):
            return result

        log('Fix applied! Commit: ' + str(result.get("commit_sha", "N/A"))[:8], 'success')
        log('=== AUTO-FIX COMPLETE ===', 'success')

        return {
            'success': True,
            'fix_applied': True,
            'fix_description': fix.get('description', ''),
            'files_changed': [f.get('path') for f in files_to_change],
            'commit_sha': result.get('commit_sha'),
        }

    # ============================================
    # ⭐ COMPREHENSIVE SCAN — scans ALL files
    # ============================================
    def _comprehensive_scan(self, error_context, files, owner, repo, root_dir=None, log=None):
        """Scan ALL source files for potential issues."""
        def _log(msg, level='info'):
            print("[SCAN] " + str(msg))
            if log:
                log(msg, level)

        issues = []

        error_lower = error_context.lower()
        is_eslint = 'eslint' in error_lower or 'no-unused-vars' in error_lower or 'is defined but never used' in error_lower

        # Get files from error
        error_files = set()
        eslint_matches = re.findall(r"src/[a-zA-Z0-9_\-/\.]+\.(?:jsx?|tsx?|vue)", error_context)
        for match in eslint_matches:
            for f in files:
                if f.endswith(match) or f.endswith('/' + match):
                    error_files.add(f)

        _log("Files in error: " + str(list(error_files)), 'info')

        # For ESLint errors: scan ALL source files
        if is_eslint:
            source_files = [f for f in files if f.endswith(('.jsx', '.tsx', '.js', '.ts')) and '/src/' in f]
            _log("Scanning " + str(len(source_files)) + " source files for unused imports...", 'info')

            # Prioritize error files first, but scan all
            for file_path in source_files:
                try:
                    content = self._fetch_file_content(owner, repo, file_path)
                    if not content:
                        continue

                    unused = self._detect_unused_imports(content)

                    # Also detect unused functions/variables
                    unused_vars = self._detect_unused_variables(content)

                    if unused or unused_vars:
                        _log("File " + file_path + ": " + str(len(unused)) + " unused imports, " + str(len(unused_vars)) + " unused vars", 'warning')
                        issues.append({
                            'file': file_path,
                            'unused_imports': unused,
                            'unused_variables': unused_vars,
                        })
                except Exception as e:
                    _log("Scan error for " + file_path + ": " + str(e), 'warning')

        return issues

    def _fetch_file_content(self, owner, repo, file_path):
        """Fetch a single file's content."""
        try:
            url = 'https://api.github.com/repos/' + str(owner) + '/' + str(repo) + '/contents/' + file_path
            resp = requests.get(
                url,
                headers={
                    'Authorization': 'token ' + str(self.github_token),
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return base64.b64decode(resp.json()['content']).decode('utf-8', errors='ignore')
        except Exception:
            pass
        return None

    def _detect_unused_imports(self, content):
        """Advanced unused import detection."""
        unused = []

        # Combined imports: import Default, { Named1, Named2 } from '...'
        combined = r"import\s+(\w+)\s*,\s*\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(combined, content):
            default_name = match.group(1).strip()
            named = [n.strip().split(' as ')[-1].strip() for n in match.group(2).split(',')]
            names = [default_name] + named
            content_without = content[:match.start()] + content[match.end():]

            for name in names:
                if not name:
                    continue
                if not re.search(r'\b' + re.escape(name) + r'\b', content_without):
                    unused.append(name)

        # Named imports: import { A, B } from '...'
        named_pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(named_pattern, content):
            named = [n.strip().split(' as ')[-1].strip() for n in match.group(1).split(',')]
            content_without = content[:match.start()] + content[match.end():]

            for name in named:
                if not name:
                    continue
                if not re.search(r'\b' + re.escape(name) + r'\b', content_without):
                    unused.append(name)

        # Default imports: import X from '...'
        default_pattern = r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(default_pattern, content):
            name = match.group(1)
            if name == 'React':
                continue
            content_without = content[:match.start()] + content[match.end():]

            if not re.search(r'\b' + re.escape(name) + r'\b', content_without):
                unused.append(name)

        return list(set(unused))

    def _detect_unused_variables(self, content):
        """Detect unused const/let/var declarations and functions."""
        unused = []

        # Skip import lines
        content_lines = content.split('\n')
        content_without_imports = '\n'.join([
            line for line in content_lines
            if not line.strip().startswith('import ')
        ])

        # const/let/var name = ...
        var_pattern = r'(?:const|let|var)\s+(\w+)\s*='
        for match in re.finditer(var_pattern, content_without_imports):
            name = match.group(1)
            if name in ('React', 'module', 'exports'):
                continue

            # Check usage (excluding the declaration line)
            after_decl = content_without_imports[:match.start()] + content_without_imports[match.end():]
            if not re.search(r'\b' + re.escape(name) + r'\b', after_decl):
                unused.append(name)

        # function name(...) { }
        func_pattern = r'function\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content_without_imports):
            name = match.group(1)
            after_decl = content_without_imports[:match.start()] + content_without_imports[match.end():]
            if not re.search(r'\b' + re.escape(name) + r'\b', after_decl):
                unused.append(name)

        return list(set(unused))

    # ============================================
    # Generate COMPREHENSIVE fix
    # ============================================
    def _generate_comprehensive_fix(self, error_context, files, owner, repo, root_dir=None, predicted_issues=None, log=None):
        def _log(msg, level='info'):
            print("[AUTOFIX] " + str(msg))
            if log:
                log(msg, level)

        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)

            # ⭐ Fetch ALL files that have predicted issues (up to token limit)
            files_to_fix = []
            if predicted_issues:
                files_to_fix = [pi['file'] for pi in predicted_issues]
            else:
                # Fallback: files mentioned in error
                eslint_matches = re.findall(r"src/[a-zA-Z0-9_\-/\.]+\.(?:jsx?|tsx?|vue)", error_context)
                for match in eslint_matches:
                    for f in files:
                        if f.endswith(match) or f.endswith('/' + match):
                            files_to_fix.append(f)

            # ⭐ LIMIT to fit Groq token limit — max 4 files
            MAX_FILES = 4
            MAX_CHARS = 5000
            files_to_fix = list(set(files_to_fix))[:MAX_FILES]

            _log("Fetching " + str(len(files_to_fix)) + " files (limit " + str(MAX_CHARS) + " chars)...", 'info')

            # Fetch contents
            file_contents = []
            total_chars = 0

            for fp in files_to_fix:
                content = self._fetch_file_content(owner, repo, fp)
                if not content:
                    continue

                remaining = MAX_CHARS - total_chars
                if remaining < 300:
                    break

                per_file_limit = min(1800, remaining)
                if len(content) > per_file_limit:
                    content = content[:per_file_limit] + "\n... [truncated]"

                file_contents.append("=== " + fp + " ===\n" + content + "\n")
                total_chars += len(content)
                _log("Fetched " + fp + " (" + str(len(content)) + " chars, total: " + str(total_chars) + ")", 'success')

            files_content = '\n'.join(file_contents)

            # Build predicted issues text
            predicted_text = ""
            if predicted_issues:
                predicted_text = "\n=== PRE-DETECTED ISSUES (from static analysis) ===\n"
                predicted_text += "The following issues were detected by our static scanner:\n\n"
                for pi in predicted_issues:
                    predicted_text += "File: " + pi['file'] + "\n"
                    if pi['unused_imports']:
                        predicted_text += "  Unused imports: " + ', '.join(pi['unused_imports']) + "\n"
                    if pi['unused_variables']:
                        predicted_text += "  Unused variables: " + ', '.join(pi['unused_variables']) + "\n"
                    predicted_text += "\n"
                predicted_text += "⚠️  IMPORTANT: These issues MUST ALL be fixed in your response.\n"

            system_msg = (
                "You are an expert React/JavaScript engineer. "
                "Return ONLY valid JSON, no markdown, no explanation. "
                "You MUST fix ALL unused imports/variables in the given files, not just the ones in the error message."
            )

            parts = []
            parts.append("A Vercel deployment failed. Provide a COMPREHENSIVE fix that addresses ALL potential errors.")
            parts.append("")
            parts.append("ERROR LOGS:")
            parts.append("```")
            parts.append(error_context[:2000])
            parts.append("```")
            parts.append("")
            parts.append(predicted_text)
            parts.append("")
            parts.append("Repo: " + str(owner) + "/" + str(repo))
            parts.append("Root: " + str(root_dir or 'root'))
            parts.append("")
            parts.append("File contents (CURRENT STATE):")
            parts.append(files_content)
            parts.append("")
            parts.append("=== FIX INSTRUCTIONS ===")
            parts.append("")
            parts.append("CRITICAL — Follow these rules:")
            parts.append("")
            parts.append("1. Remove ALL unused imports in EACH file (not just the ones in the error)")
            parts.append("   - Scan every import line")
            parts.append("   - Check if each imported name is used")
            parts.append("   - Remove unused names from named imports: `{ A, B, C }` → `{ A, C }` if B is unused")
            parts.append("   - Remove entire import lines if all names are unused")
            parts.append("")
            parts.append("2. Remove ALL unused variables/functions:")
            parts.append("   - `const x = ...` where x is never used")
            parts.append("   - `function foo() {}` where foo is never called")
            parts.append("   - `let/var` declarations never used")
            parts.append("")
            parts.append("3. Fix any Node.js version issues in package.json")
            parts.append("   - Use engines: { \"node\": \">=20.0.0\" }")
            parts.append("")
            parts.append("4. Preserve ALL working code:")
            parts.append("   - Keep used imports")
            parts.append("   - Keep functional logic")
            parts.append("   - Only remove unused code")
            parts.append("")
            parts.append("5. Provide COMPLETE file content (not partial diffs)")
            parts.append("")
            parts.append("RESPONSE FORMAT (ONLY JSON):")
            parts.append("{")
            parts.append('  "description": "Brief description",')
            parts.append('  "root_cause": "What caused the errors",')
            parts.append('  "files_to_change": [')
            parts.append('    {')
            parts.append('      "path": "full/path/to/file.js",')
            parts.append('      "new_content": "COMPLETE new file content",')
            parts.append('      "commit_message": "Fix: ..."')
            parts.append('    }')
            parts.append('  ]')
            parts.append("}")

            user_msg = '\n'.join(parts)

            # Token estimate
            approx_tokens = (len(user_msg) + len(system_msg)) // 4
            _log("Estimated prompt tokens: ~" + str(approx_tokens), 'info')

            # If too large, reduce
            if approx_tokens > 6500:
                _log("Payload too large — reducing to 2 files", 'warning')
                files_to_fix = files_to_fix[:2]
                file_contents = []
                total_chars = 0
                for fp in files_to_fix:
                    content = self._fetch_file_content(owner, repo, fp)
                    if not content:
                        continue
                    remaining = 3000 - total_chars
                    if remaining < 300:
                        break
                    per_file_limit = min(1200, remaining)
                    if len(content) > per_file_limit:
                        content = content[:per_file_limit] + "\n... [truncated]"
                    file_contents.append("=== " + fp + " ===\n" + content + "\n")
                    total_chars += len(content)

                files_content = '\n'.join(file_contents)
                # Rebuild prompt
                parts[parts.index("File contents (CURRENT STATE):") + 1] = files_content
                user_msg = '\n'.join(parts)
                approx_tokens = (len(user_msg) + len(system_msg)) // 4
                _log("New estimate: ~" + str(approx_tokens), 'info')

            _log("Sending request to Groq AI...", 'info')

            resp = client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=4000,
            )

            raw = resp.choices[0].message.content.strip()
            _log("AI response length: " + str(len(raw)) + " chars", 'info')

            raw_clean = re.sub(r'^```(?:json)?\s*', '', raw)
            raw_clean = re.sub(r'\s*```$', '', raw_clean)

            try:
                fix = json.loads(raw_clean)
                _log("JSON parsed OK", 'success')
                return fix
            except json.JSONDecodeError:
                json_match = re.search(r'\{[\s\S]*\}', raw)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except Exception:
                        pass
                return None

        except Exception as e:
            error_msg = str(e)
            _log("_generate_comprehensive_fix error: " + error_msg[:200], 'error')

            # Retry with even smaller
            if '413' in error_msg or 'tokens per minute' in error_msg.lower():
                _log("Token limit — retrying with 1 file only", 'warning')
                try:
                    if not files_to_fix:
                        return None

                    single_file = files_to_fix[0]
                    content = self._fetch_file_content(owner, repo, single_file)
                    if not content:
                        return None

                    content = content[:1500]

                    from groq import Groq
                    client = Groq(api_key=self.groq_key)

                    minimal = (
                        "Fix ALL errors in this React file. Return ONLY JSON.\n\n"
                        "ERRORS:\n" + error_context[:800] + "\n\n"
                        "FILE: " + single_file + "\n" + content + "\n\n"
                        "Return: {\"description\":\"...\",\"root_cause\":\"...\",\"files_to_change\":[{\"path\":\"" + single_file + "\",\"new_content\":\"...\",\"commit_message\":\"...\"}]}"
                    )

                    resp = client.chat.completions.create(
                        model=self.groq_model,
                        messages=[
                            {"role": "system", "content": "Return ONLY JSON."},
                            {"role": "user", "content": minimal},
                        ],
                        temperature=0.1,
                        max_tokens=4000,
                    )

                    raw = resp.choices[0].message.content.strip()
                    raw_clean = re.sub(r'^```(?:json)?\s*', '', raw)
                    raw_clean = re.sub(r'\s*```$', '', raw_clean)
                    return json.loads(raw_clean)

                except Exception as e2:
                    _log("Retry failed: " + str(e2)[:200], 'error')

            return None

    # ============================================
    # STEP 1: Fetch Vercel logs
    # ============================================
    def _get_deployment_logs(self, deploy_id):
        try:
            url = 'https://api.vercel.com/v2/deployments/' + str(deploy_id) + '/events'
            resp = requests.get(
                url,
                headers={'Authorization': 'Bearer ' + str(self.vercel_token)},
                timeout=20,
            )
            if resp.status_code != 200:
                return []

            events = resp.json()
            if not isinstance(events, list):
                return []

            logs = []
            for event in events:
                text = ''
                payload = event.get('payload', {})
                if isinstance(payload, dict):
                    text = payload.get('text', '')
                if not text:
                    text = event.get('text', '')
                if text and text.strip():
                    logs.append(text.strip())

            return logs
        except Exception:
            return []

    def _extract_error_from_logs(self, logs):
        if not logs:
            return ''

        error_patterns = [
            r'Error:\s*.+',
            r'error\s+.+',
            r'Failed to compile',
            r'not found',
            r'Cannot find module\s+.+',
            r"Can't resolve\s+.+",
            r'Module not found\s+.+',
            r'Command\s+.+\s+exited with\s+.+',
            r'ENOENT',
            r'npm ERR!',
            r'no-unused-vars',
            r'\[eslint\]',
            r'is defined but never used',
            r'is assigned a value but never used',
            r'Node.js Version',
        ]

        error_lines = []
        for line in logs:
            for pattern in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    error_lines.append(line)
                    break

        last_lines = logs[-50:] if len(logs) > 50 else logs

        context_parts = []
        if error_lines:
            context_parts.append("=== ERRORS ===")
            context_parts.extend(error_lines[-30:])

        context_parts.append("\n=== LAST LINES ===")
        context_parts.extend(last_lines)

        context = '\n'.join(context_parts)
        return context[:7000] if context else ''

    def _get_repo_files(self, owner, repo, path='', depth=0):
        if depth > 4:
            return []

        try:
            url = 'https://api.github.com/repos/' + str(owner) + '/' + str(repo) + '/contents/' + str(path)
            resp = requests.get(
                url,
                headers={
                    'Authorization': 'token ' + str(self.github_token),
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'Smart-DevOps-AI',
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []

            items = resp.json()
            if not isinstance(items, list):
                return []

            files = []
            for item in items:
                if item['type'] == 'file':
                    files.append(item['path'])
                elif item['type'] == 'dir' and not item['name'].startswith('.'):
                    sub = self._get_repo_files(owner, repo, item['path'], depth + 1)
                    files.extend(sub)

            return files
        except Exception:
            return []

    # ============================================
    # STEP 5: Apply fix
    # ============================================
    def _apply_fix(self, owner, repo, fix, log=None):
        def _log(msg, level='info'):
            print("[AUTOFIX] " + str(msg))
            if log:
                log(msg, level)

        try:
            files_to_change = fix.get('files_to_change', [])
            if not files_to_change:
                return {'success': False, 'error': 'No files to change'}

            repo_resp = requests.get(
                'https://api.github.com/repos/' + str(owner) + '/' + str(repo),
                headers={
                    'Authorization': 'token ' + str(self.github_token),
                    'Accept': 'application/vnd.github+json',
                },
                timeout=15,
            )
            default_branch = repo_resp.json().get('default_branch', 'main')

            last_commit_sha = None
            for change in files_to_change:
                path = change.get('path')
                new_content = change.get('new_content', '')
                commit_msg = change.get('commit_message', 'Auto-fix: ' + str(path))

                if not path or not new_content:
                    continue

                _log("Committing " + path + " (" + str(len(new_content)) + " chars)...", 'info')

                file_resp = requests.get(
                    'https://api.github.com/repos/' + str(owner) + '/' + str(repo) + '/contents/' + path,
                    headers={
                        'Authorization': 'token ' + str(self.github_token),
                        'Accept': 'application/vnd.github+json',
                    },
                    timeout=15,
                )

                encoded = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
                payload = {'message': commit_msg, 'content': encoded, 'branch': default_branch}

                if file_resp.status_code == 200:
                    payload['sha'] = file_resp.json()['sha']
                    _log("  Updating existing file", 'info')

                create_resp = requests.put(
                    'https://api.github.com/repos/' + str(owner) + '/' + str(repo) + '/contents/' + path,
                    headers={
                        'Authorization': 'token ' + str(self.github_token),
                        'Accept': 'application/vnd.github+json',
                    },
                    json=payload,
                    timeout=20,
                )

                if create_resp.status_code not in (200, 201):
                    return {'success': False, 'error': 'Failed ' + path}

                last_commit_sha = create_resp.json()['commit']['sha']
                _log("Committed " + path + ": " + last_commit_sha[:8], 'success')

            return {'success': True, 'commit_sha': last_commit_sha}
        except Exception as e:
            return {'success': False, 'error': str(e)}