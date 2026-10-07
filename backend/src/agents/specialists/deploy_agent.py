"""
DeployAgent — Agentic Multi-Provider Deployment with Auto-Fix
=============================================================
Self-host (default) + Vercel/Render/Netlify/DockerHub
+ ErrorRecoveryAgent integration for auto-fix + retry

NEW: ErrorRecoveryAgent wrap for self-healing deployments
"""

import os
import sys
import re
import time
from typing import Dict, Any, Optional

from ..base_agent import BaseAgent

# Fix imports
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


class DeployAgent(BaseAgent):
    """Agentic Multi-Provider Deployment Agent with Auto-Fix."""

    SUPPORTED_PROVIDERS = [
        'self-host', 'selfhost', 'self_host',
        'vercel', 'render', 'netlify', 'dockerhub',
    ]

    NON_DEPLOY_MODES = ['ci-cd-only']

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'DeployAgent',
            config={
                **(config or {}),
                'role': 'deployment specialist with self-healing',
                'goal': 'Deploy apps with automatic error recovery',
                'capabilities': [
                    'deploy_fullstack', 'self_host', 'deploy_vercel',
                    'deploy_render', 'deploy_netlify', 'deploy_dockerhub',
                    'auto_fix_deploy', 'self_healing_deploy',
                ],
                'max_retries': 3,
            }
        )
        self.total_deployments = 0
        self.successful_deployments = 0
        self.failed_deployments = 0
        self.auto_fixed_deployments = 0

    # ============================================
    # MAIN
    # ============================================
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        context = context or {}
        sid = context.get('sid')

        if not isinstance(input_data, dict):
            return {'success': False, 'error': 'Input must be a dict'}

        repo_url = input_data.get('repo_url')
        deploy_type = input_data.get('deploy_type', 'auto')
        fullstack = input_data.get('fullstack', deploy_type in ('auto', 'fullstack'))
        deploy_method = input_data.get('deploy_method', 'self-host')
        provider = input_data.get('provider', 'auto')
        mode = input_data.get('mode', 'self-deploy')

        # Guard: ci-cd-only mode
        if mode in self.NON_DEPLOY_MODES:
            msg = f"⏭️ Mode '{mode}' is CI/CD only — deploy is skipped"
            self.emit_log(msg, "warning", sid)
            return {
                'success': True,
                'type': 'deploy',
                'status': 'skipped',
                'mode': mode,
                'repo': repo_url,
                'message': msg,
                'live_url': None,
                'response': f"## ⏭️ Deploy Skipped\n\n**Reason:** Mode `{mode}` is CI/CD only.",
            }

        if input_data.get('skip_deploy', False):
            self.emit_log("⏭️ skip_deploy=True — skipping", "warning", sid)
            return {
                'success': True, 'type': 'deploy', 'status': 'skipped',
                'mode': mode, 'live_url': None,
                'response': "## ⏭️ Deploy Skipped",
            }

        self.emit_log("=" * 60, "info", sid)
        self.emit_log("🚀 DeployAgent started (with Auto-Fix)", "info", sid)
        self.emit_log(f"📦 Repo: {repo_url}", "info", sid)
        self.emit_log(f"🎯 Mode: {mode}", "info", sid)
        self.emit_log(f"🎯 Type: {deploy_type}", "info", sid)
        self.emit_log(f"🚀 Method: {deploy_method} / {provider}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        if not repo_url:
            return {'success': False, 'error': 'No repo_url provided'}

        start_time = time.time()
        self.clear_working_memory()

        try:
            # STEP 1: Parse URL
            self.emit_log("", "info", sid)
            self.emit_log("📌 STEP 1/4: Parsing GitHub URL", "info", sid)
            parsed = self.use_tool('github_parse_url', url=repo_url)
            if not parsed.get('success'):
                return {'success': False, 'error': 'Invalid GitHub URL'}
            owner = parsed['owner']
            repo = parsed['repo']
            self.emit_log(f"   Owner: {owner}, Repo: {repo}", "info", sid)

            # STEP 2: Fetch metadata
            self.emit_log("", "info", sid)
            self.emit_log("📌 STEP 2/4: Fetching repo metadata", "info", sid)
            repo_info = self.use_tool('github_get_repo_info', owner=owner, repo=repo)
            if not repo_info.get('success'):
                return {'success': False, 'error': 'Could not fetch repo info'}
            default_branch = repo_info.get('default_branch', 'main')
            self.emit_log(f"   ✅ Branch: {default_branch}", "success", sid)

            # STEP 3: Detect stack
            self.emit_log("", "info", sid)
            self.emit_log("📌 STEP 3/4: Detecting stack", "info", sid)
            clone_result = self.use_tool('github_clone', owner=owner, repo=repo, branch=default_branch)
            if not clone_result.get('success'):
                return {'success': False, 'error': 'Clone failed'}
            repo_path = clone_result.get('path')
            stack_result = self.use_tool('detect_stack', repo_path=repo_path)
            stack_type = stack_result.get('type', 'node')
            framework = stack_result.get('framework', 'unknown')
            root_dir = stack_result.get('root_dir')
            self.emit_log(f"   Stack: {stack_type} ({framework})", "success", sid)

            # STEP 4: Deploy with Auto-Fix
            self.emit_log("", "info", sid)
            self.emit_log("📌 STEP 4/4: Deploying (with auto-fix)", "info", sid)

            actual_provider = self._resolve_provider(provider, deploy_method)
            self.emit_log(f"   🎯 Resolved provider: {actual_provider}", "info", sid)

            # Build the deploy callable
            def _do_deploy():
                if actual_provider == 'self-host':
                    try:
                        from src.services.self_host_service import SelfHostService
                        deployer = SelfHostService(agent=self)

                        return deployer.deploy(
                            owner=owner, repo=repo, repo_url=repo_url,
                            default_branch=default_branch,
                            stack_info={
                                'type': stack_type,
                                'framework': framework,
                                'root_dir': root_dir,
                                'frontend_dir': root_dir,
                                'deploy_type': deploy_type,
                            },
                            sid=sid,
                            on_log=lambda msg, level='info': self.emit_log(msg, level, sid),
                        )
                    except Exception as e:
                        self.emit_log(f"   ⚠️ Self-host error: {str(e)[:150]}", "warning", sid)
                        import traceback
                        traceback.print_exc()
                        return {'success': False, 'error': str(e)}
                else:
                    try:
                        from src.services.multi_provider_deploy import MultiProviderDeployService
                        deployer = MultiProviderDeployService(agent=self)

                        return deployer.deploy(
                            provider=actual_provider,
                            owner=owner, repo=repo, repo_url=repo_url,
                            default_branch=default_branch,
                            stack_info={
                                'type': stack_type,
                                'framework': framework,
                                'root_dir': root_dir,
                            },
                            sid=sid,
                            on_log=lambda msg, level='info': self.emit_log(msg, level, sid),
                        )
                    except Exception as e:
                        self.emit_log(f"   ⚠️ Provider error: {str(e)[:150]}", "warning", sid)
                        import traceback
                        traceback.print_exc()
                        return {'success': False, 'error': str(e)}

            # Wrap with ErrorRecoveryAgent
            try:
                from src.agents.specialists.error_recovery_agent import ErrorRecoveryAgent
                recovery = ErrorRecoveryAgent()

                deploy_result = recovery.process(
                    {
                        'action_fn': _do_deploy,
                        'action_name': f'deploy_{owner}_{repo}',
                        'repo_url': repo_url,
                        'error_logs': '',
                        'max_attempts': 3,
                    },
                    context={
                        'sid': sid,
                        'user_id': context.get('user_id'),
                        'project_id': context.get('project_id'),
                        'project_name': repo,
                    },
                )
            except Exception as e:
                self.emit_log(f"   ⚠️ Recovery agent error: {str(e)[:150]}", "warning", sid)
                import traceback
                traceback.print_exc()
                deploy_result = _do_deploy()

            # Build response
            elapsed = time.time() - start_time
            self.total_deployments += 1

            recovery_info = deploy_result.get('recovery', {}) if isinstance(deploy_result, dict) else {}
            auto_fixes = recovery_info.get('auto_fixes_applied', 0)
            if auto_fixes > 0:
                self.auto_fixed_deployments += 1

            if deploy_result and deploy_result.get('success'):
                self.successful_deployments += 1
                self.track_metric(True, elapsed)
                url = deploy_result.get('url') or deploy_result.get('primary_url') or 'N/A'

                self.emit_log("", "info", sid)
                self.emit_log("=" * 60, "success", sid)
                self.emit_log(f"🎉 DEPLOYED in {elapsed:.1f}s", "success", sid)
                if auto_fixes > 0:
                    self.emit_log(f"   🔧 Auto-fixes applied: {auto_fixes}", "success", sid)
                self.emit_log(f"   URL: {url}", "success", sid)
                self.emit_log("=" * 60, "success", sid)

                response_md = (
                    f"## 🎉 Deployment Successful!\n\n"
                    f"**Repo:** [{owner}/{repo}]({repo_url})\n"
                    f"**Mode:** `{mode}`\n"
                    f"**Type:** `{deploy_type}`\n"
                    f"**Provider:** `{actual_provider}`\n"
                    f"**Stack:** `{stack_type}` ({framework})\n"
                )
                if auto_fixes > 0:
                    response_md += f"**Auto-fixes:** {auto_fixes} 🔧\n"
                response_md += f"\n### 🌐 Live URL\n[{url}]({url})\n\n"

                if deploy_result.get('frontend_url') or deploy_result.get('backend_url'):
                    response_md += "### Services\n"
                    if deploy_result.get('frontend_url'):
                        response_md += f"- 🎨 Frontend: [{deploy_result['frontend_url']}]({deploy_result['frontend_url']})\n"
                    if deploy_result.get('backend_url'):
                        response_md += f"- ⚙️ Backend: [{deploy_result['backend_url']}]({deploy_result['backend_url']})\n"

                return {
                    'success': True,
                    'type': 'deploy',
                    'status': 'deployed',
                    'mode': mode,
                    'repo': f'{owner}/{repo}',
                    'provider': actual_provider,
                    'deploy_type': deploy_type,
                    'url': url,
                    'live_url': url,
                    'primary_url': url,
                    'frontend_url': deploy_result.get('frontend_url'),
                    'backend_url': deploy_result.get('backend_url'),
                    'duration': f'{elapsed:.1f}s',
                    'auto_fixes_applied': auto_fixes,
                    'recovery_attempts': recovery_info.get('attempts', 1),
                    'response': response_md,
                }
            else:
                self.failed_deployments += 1
                self.track_metric(False, elapsed)
                error = (deploy_result or {}).get('error', 'Unknown error')

                self.emit_log(f"❌ DEPLOY FAILED: {error[:200]}", "error", sid)

                return {
                    'success': False,
                    'type': 'deploy',
                    'status': 'failed',
                    'mode': mode,
                    'repo': f'{owner}/{repo}',
                    'error': error,
                    'duration': f'{elapsed:.1f}s',
                    'response': f"## ⚠️ Deployment Failed\n\n**Error:** {error[:300]}",
                }

        except Exception as e:
            elapsed = time.time() - start_time
            self.failed_deployments += 1
            self.track_metric(False, elapsed)
            self.emit_log(f"❌ Fatal: {str(e)[:200]}", "error", sid)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    # ============================================
    # Provider resolution
    # ============================================
    def _resolve_provider(self, provider: str, deploy_method: str) -> str:
        p = (provider or '').lower().strip()
        m = (deploy_method or '').lower().strip()

        if p in ('', 'auto') and m in ('', 'auto', 'self-host'):
            return 'self-host'
        if p and p not in ('auto', ''):
            return self._normalize(p)
        if m and m not in ('auto', ''):
            return self._normalize(m)
        return 'self-host'

    def _normalize(self, name: str) -> str:
        n = name.lower().strip()
        aliases = {
            'selfhost': 'self-host',
            'self_host': 'self-host',
            'self host': 'self-host',
            'vercel.com': 'vercel',
            'render.com': 'render',
            'netlify.com': 'netlify',
            'docker': 'dockerhub',
            'docker-hub': 'dockerhub',
        }
        return aliases.get(n, n)

    def get_metrics(self) -> Dict:
        base = super().get_metrics()
        return {
            **base,
            'total_deployments': self.total_deployments,
            'successful_deployments': self.successful_deployments,
            'failed_deployments': self.failed_deployments,
            'auto_fixed_deployments': self.auto_fixed_deployments,
            'success_rate': (
                (self.successful_deployments / self.total_deployments * 100)
                if self.total_deployments > 0 else 0
            ),
        }