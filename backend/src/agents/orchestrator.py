"""
Orchestrator - Agentic Multi-Agent Coordinator
LLM-powered routing + Multi-step workflows + All specialists

Mode-aware routing:
    - ci-cd-only      -> pipeline only, no deploy
    - self-deploy     -> deploy only, skip pipeline
    - ci-cd+deploy    -> full pipeline + deploy (DEFAULT for pipeline)
    - custom-deploy   -> deploy to specific provider

All actions route through agents (no direct service calls).
"""

import os
import sys
import json
import re
import time
import traceback
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent

# Fix: Add backend root to sys.path
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# Specialists
from .specialists.deploy_agent import DeployAgent
from .specialists.pipeline_agent import PipelineAgent
from .specialists.healer_agent import HealerAgent
from .specialists.monitor_agent import MonitorAgent
from .specialists.security_agent import SecurityAgent
from .specialists.code_fixer_agent import CodeFixerAgent
from .specialists.error_recovery_agent import ErrorRecoveryAgent
from .specialists.scale_agent import ScaleAgent

# Legacy agents
try:
    from .analyzer_agent import AnalyzerAgent
    from .planner_agent import PlannerAgent
except ImportError:
    AnalyzerAgent = None
    PlannerAgent = None


class Orchestrator(BaseAgent):
    """Agentic Multi-Agent Coordinator - Mode-aware."""

    # Content improvement keywords
    IMPROVE_KEYWORDS = [
        'improve content', 'improve the content', 'improve my app',
        'improve app', 'enhance content', 'replace placeholder',
        'fix placeholder', 'improve placeholder', 'better content',
        'improve website', 'improve site', 'enhance website',
        'make it better', 'improve ui', 'improve page',
        'improve this app', 'improve the app',
    ]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            'Orchestrator',
            config={
                **(config or {}),
                'role': 'multi-agent coordinator',
                'goal': 'Route tasks to specialist agents and orchestrate workflows',
            }
        )

        self.agents = {
            'deploy': DeployAgent(config),
            'pipeline': PipelineAgent(config),
            'healer': HealerAgent(config),
            'monitor': MonitorAgent(config),
            'security': SecurityAgent(config),
            'code_fixer': CodeFixerAgent(config),
            'error_recovery': ErrorRecoveryAgent(config),
            'scale': ScaleAgent(config),
        }

        if AnalyzerAgent:
            self.agents['analyzer'] = AnalyzerAgent(config)
        if PlannerAgent:
            self.agents['planner'] = PlannerAgent(config)

        self.task_queue = []
        self.active_executions = {}

        # Self-host service
        try:
            from src.services.self_host_service import SelfHostService
            self.self_host = SelfHostService(agent=self)
            self.emit_log("   SelfHostService initialized", "info")
        except Exception as e:
            self.self_host = None
            self.emit_log(f"   SelfHostService failed: {str(e)[:100]}", "warning")

        self.emit_log(
            f"Orchestrator initialized with {len(self.agents)} agents",
            "success"
        )
        for name, agent in self.agents.items():
            self.emit_log(f"   - {name}: {agent.name}", "info")

    # ============================================
    # Main Process
    # ============================================
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """Main entry point."""
        context = context or {}
        sid = context.get('sid')
        start_time = time.time()

        preview = (
            str(input_data)[:80]
            if not isinstance(input_data, dict)
            else json.dumps(input_data, default=str)[:80]
        )
        self.emit_log("=" * 60, "info", sid)
        self.emit_log(f"Orchestrator received: {preview}", "info", sid)
        self.emit_log("=" * 60, "info", sid)

        try:
            input_type = self._classify_input(input_data)
            self.emit_log(f"Classification: [{input_type.upper()}]", "info", sid)

            if input_type == 'file_upload':
                return self._handle_file_upload(input_data, context, sid)
            elif input_type == 'devops_command':
                return self._handle_devops_command(input_data, context, sid)
            elif input_type == 'webhook':
                return self._handle_webhook(input_data, context, sid)
            elif input_type == 'natural_language':
                return self._handle_natural_language(input_data, context, sid)
            else:
                return self._handle_general(input_data, context, sid)

        except Exception as e:
            elapsed = time.time() - start_time
            self.track_metric(False, elapsed)
            self.emit_log(f"Fatal: {str(e)[:200]}", "error", sid)
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    # ============================================
    # Classify Input
    # ============================================
    def _classify_input(self, input_data: Any) -> str:
        if isinstance(input_data, dict):
            if 'files' in input_data or 'file' in input_data:
                return 'file_upload'
            if 'webhook' in input_data or 'repository' in input_data:
                return 'webhook'
            if 'command' in input_data or 'action' in input_data:
                if input_data.get('action') == 'chat' or 'query' in input_data:
                    return 'natural_language'
                return 'devops_command'
        if isinstance(input_data, str):
            if input_data.startswith('{'):
                try:
                    json.loads(input_data)
                    return 'devops_command'
                except Exception:
                    pass
            return 'natural_language'
        return 'general'

    # ============================================
    # Natural Language Handler
    # ============================================
    def _handle_natural_language(self, input_data, context, sid=None):
        """Parse NL, route to correct agent with LLM."""
        context = context or {}

        if isinstance(input_data, dict):
            text = input_data.get('query', input_data.get('command', ''))
        else:
            text = str(input_data)

        text_lower = text.lower()

        # Detect code snippet
        code_snippet = self._extract_code_block(text)
        if code_snippet and self._looks_like_code_fix_request(text):
            self.emit_log("Code fix request -> CodeFixerAgent", "info", sid)
            return self._delegate_to_code_fixer(text, code_snippet, context, sid)

        # Extract GitHub URL
        github_url = self._extract_github_url(text)
        if github_url:
            self.remember('repo_url', github_url)
            self.emit_log(f"GitHub URL: {github_url}", "info", sid)

        # Content improvement check (HIGH PRIORITY)
        if any(kw in text_lower for kw in self.IMPROVE_KEYWORDS) and github_url:
            self.emit_log("Content improvement request -> HealerAgent (improve mode)", "info", sid)
            return self._delegate_to_improve_content(text, github_url, context, sid)

        # Check for errors
        has_error = self._detect_error_in_text(text)
        if has_error and github_url:
            self.emit_log("Error detected -> HealerAgent", "warning", sid)
            return self._delegate_to_healer(text, context, sid)

        # LLM routing
        self.emit_log("Using LLM for routing...", "info", sid)
        decision = self._route_with_llm(text, sid)
        if not decision:
            decision = self._route_with_rules(text)
            self.emit_log(f"Rule-based: {decision}", "info", sid)

        action = decision.get('agent', 'general')
        reasoning = decision.get('reasoning', '')
        self.emit_log(f"Routed to: {action}", "success", sid)
        self.emit_log(f"{reasoning}", "info", sid)

        if action == 'deploy':
            return self._delegate_to_deploy(text, github_url, context, sid)
        elif action == 'pipeline':
            return self._delegate_to_pipeline(text, github_url, context, sid)
        elif action == 'security':
            return self._delegate_to_security(text, github_url, context, sid)
        elif action == 'monitor':
            return self._delegate_to_monitor(text, context, sid)
        elif action == 'healer':
            return self._delegate_to_healer(text, context, sid)
        elif action == 'improve_content':
            return self._delegate_to_improve_content(text, github_url, context, sid)
        elif action == 'code_fixer':
            return self._delegate_to_code_fixer(text, code_snippet, context, sid)
        elif action == 'error_recovery':
            return self._delegate_to_error_recovery(text, github_url, context, sid)
        elif action == 'analyze':
            return self._delegate_to_analyzer(text, github_url, context, sid)
        else:
            return self._execute_general(text, context, sid)

    # ============================================
    # LLM Router
    # ============================================
    def _route_with_llm(self, text: str, sid=None) -> Optional[Dict]:
        prompt = f"""You are an orchestrator routing user requests to specialist agents.

User request: "{text}"

Available agents:
- deploy: Deploy applications to cloud (no CI/CD)
- pipeline: Create CI/CD pipelines (may or may not deploy)
- healer: Fix errors IN A GITHUB REPO (has URL)
- improve_content: Improve/Replace PLACEHOLDER CONTENT in a repo
- code_fixer: Fix a USER-PROVIDED code snippet
- error_recovery: Universal error recovery
- monitor: Monitor applications
- security: Security scans
- analyzer: Code analysis

IMPORTANT:
- "improve_content" -> if user wants to IMPROVE CONTENT or REPLACE PLACEHOLDER
- "code_fixer" -> if user pastes CODE BLOCK
- "healer" -> if user wants REPO errors fixed
- "pipeline" -> CI/CD creation
- "deploy" -> deploy an app (no pipeline)

Respond ONLY with JSON:
{{
  "agent": "deploy" | "pipeline" | "healer" | "improve_content" | "code_fixer" | "error_recovery" | "monitor" | "security" | "analyzer" | "general",
  "reasoning": "Brief explanation",
  "confidence": 0.0-1.0
}}"""

        response = self.call_llm(prompt, expect_json=True)
        if not response:
            return None

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def _route_with_rules(self, text: str) -> Dict:
        text_lower = text.lower()

        if self._extract_code_block(text) and any(
            w in text_lower for w in ['fix', 'debug', 'repair', 'optimize', 'refactor']
        ):
            return {'agent': 'code_fixer', 'reasoning': 'Code block + fix intent', 'confidence': 0.95}

        # Content improvement
        if any(w in text_lower for w in self.IMPROVE_KEYWORDS):
            return {'agent': 'improve_content', 'reasoning': 'Improve content keyword', 'confidence': 0.95}

        if any(w in text_lower for w in ['deploy', 'release', 'publish', 'ship']):
            return {'agent': 'deploy', 'reasoning': 'Deploy keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['pipeline', 'ci/cd', 'cicd', 'workflow']):
            return {'agent': 'pipeline', 'reasoning': 'Pipeline keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['fix', 'repair', 'debug', 'error', 'broken']):
            return {'agent': 'healer', 'reasoning': 'Fix keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['security', 'scan', 'vulnerability', 'audit']):
            return {'agent': 'security', 'reasoning': 'Security keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['monitor', 'health', 'uptime', 'status']):
            return {'agent': 'monitor', 'reasoning': 'Monitor keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['scale', 'replicas', 'instances']):
            return {'agent': 'scale', 'reasoning': 'Scale keyword', 'confidence': 0.9}
        if any(w in text_lower for w in ['analyze', 'inspect', 'review']):
            return {'agent': 'analyzer', 'reasoning': 'Analyze keyword', 'confidence': 0.9}

        return {'agent': 'general', 'reasoning': 'No specific action', 'confidence': 0.5}

    # ============================================
    # Delegation Methods
    # ============================================
    def _delegate_to_deploy(self, text, github_url, context, sid):
        context = context or {}
        if not github_url:
            return self._error_response("Deploy requires a GitHub URL.", sid)

        text_lower = text.lower()
        provider = 'auto'
        if 'vercel' in text_lower:
            provider = 'vercel'
        elif 'netlify' in text_lower:
            provider = 'netlify'
        elif 'render' in text_lower:
            provider = 'render'
        elif 'docker' in text_lower:
            provider = 'dockerhub'
        elif 'self-host' in text_lower or 'self host' in text_lower:
            provider = 'self-host'

        deploy_type = 'auto'
        if 'frontend only' in text_lower:
            deploy_type = 'frontend'
        elif 'backend only' in text_lower:
            deploy_type = 'backend'
        elif 'fullstack' in text_lower:
            deploy_type = 'fullstack'

        mode = 'self-deploy'
        if provider not in ('auto', 'self-host'):
            mode = 'custom-deploy'

        return self.delegate_to_agent(
            self.agents['deploy'],
            {
                'action': 'deploy',
                'repo_url': github_url,
                'project_name': self._extract_project_name(github_url),
                'mode': mode,
                'provider': provider,
                'deploy_method': provider,
                'deploy_type': deploy_type,
                'fullstack': deploy_type in ('auto', 'fullstack'),
                'skip_pipeline': True,
            },
            {**context, 'sid': sid},
        )

    # ============================================
    # PIPELINE — UPDATED: Default to ci-cd+deploy (pipeline + deploy)
    # ============================================
    def _delegate_to_pipeline(self, text, github_url, context, sid):
        """
        Delegate to PipelineAgent.

        Default mode: ci-cd+deploy (pipeline + deploy — standard CI/CD)
        Only if user explicitly says "only", "no deploy", "without deploy"
        → switch to ci-cd-only (pipeline only).
        """
        context = context or {}
        if not github_url:
            return self._error_response("Pipeline requires a GitHub URL.", sid)

        text_lower = text.lower()

        # ⭐ DEFAULT: ci-cd+deploy (pipeline + deploy)
        mode = 'ci-cd+deploy'

        # Check for ONLY-pipeline indicators → override to ci-cd-only
        only_indicators = [
            'ci/cd only', 'ci-cd only', 'pipeline only',
            'just pipeline', 'just ci/cd', 'only pipeline',
            'pipeline without deploy', 'no deploy', 'without deploy',
            "don't deploy", 'dont deploy', 'skip deploy',
            'no deployment', 'without deployment',
            'pipeline only mode', 'ci/cd only mode',
        ]
        if any(kw in text_lower for kw in only_indicators):
            mode = 'ci-cd-only'

        # Check for FULL pipeline indicators → ci-cd+deploy (explicit)
        full_indicators = [
            'ci/cd + deploy', 'ci-cd+deploy', 'pipeline + deploy',
            'full pipeline', 'ci/cd and deploy', 'and deploy',
            'with deploy', 'auto-deploy', 'auto deploy',
            'build and deploy', 'build + deploy', 'then deploy',
            'deploy after', 'deploy when', 'pipeline with deploy',
            'create pipeline + deploy', 'pipeline and deploy',
            'create pipeline and deploy', 'create ci/cd and deploy',
        ]
        if any(kw in text_lower for kw in full_indicators):
            mode = 'ci-cd+deploy'

        # Deploy method detection
        deploy_method = 'self-host'
        if 'vercel' in text_lower:
            deploy_method = 'vercel'
        elif 'netlify' in text_lower:
            deploy_method = 'netlify'
        elif 'render' in text_lower:
            deploy_method = 'render'
        elif 'docker' in text_lower:
            deploy_method = 'dockerhub'

        # Max fix attempts
        max_attempts = 50
        m = re.search(r'max(?:\s+fix)?\s+attempts?\s*[:=]?\s*(\d+)', text_lower)
        if m:
            try:
                max_attempts = int(m.group(1))
            except Exception:
                pass

        # Determine flags
        should_deploy = mode in ('ci-cd+deploy', 'self-deploy', 'custom-deploy')
        should_run_pipeline = mode in ('ci-cd-only', 'ci-cd+deploy')
        should_skip_pipeline = mode in ('self-deploy', 'custom-deploy')

        self.emit_log(
            f"   Pipeline mode: {mode} (pipeline={should_run_pipeline}, deploy={should_deploy})",
            "info", sid
        )

        return self.delegate_to_agent(
            self.agents['pipeline'],
            {
                'action': 'create',
                'repo_url': github_url,
                'mode': mode,
                'deploy_method': deploy_method,
                'provider': deploy_method,
                'max_fix_attempts': max_attempts,
                'auto_deploy': should_deploy,
                'run_pipeline': should_run_pipeline,
                'skip_pipeline': should_skip_pipeline,
            },
            {**context, 'sid': sid},
        )

    def _delegate_to_security(self, text, github_url, context, sid):
        context = context or {}
        if not github_url:
            return self._error_response("Security scan requires a GitHub URL.", sid)

        return self.delegate_to_agent(
            self.agents['security'],
            {
                'action': 'scan',
                'repo_url': github_url,
                'branch': context.get('branch'),
            },
            {**context, 'sid': sid},
        )

    def _delegate_to_monitor(self, text, context, sid):
        context = context or {}
        url_match = re.search(r'https?://[^\s]+', text or '')
        if not url_match:
            return self._error_response("Monitor requires a URL.", sid)

        return self.delegate_to_agent(
            self.agents['monitor'],
            {'action': 'check', 'urls': [url_match.group(0)]},
            {**context, 'sid': sid},
        )

    def _delegate_to_healer(self, text, context, sid):
        context = context or {}
        github_url = self._extract_github_url(text)
        if not github_url:
            return self._error_response("Healer requires a GitHub URL with error details.", sid)

        error_context = context.get('error_message', text)

        return self.delegate_to_agent(
            self.agents['healer'],
            {
                'action': 'fix',
                'repo_url': github_url,
                'error_message': error_context,
                'error_logs': context.get('error_logs', ''),
            },
            {**context, 'sid': sid},
        )

    # ============================================
    # Delegate to improve_content
    # ============================================
    def _delegate_to_improve_content(self, text, github_url, context, sid):
        """Delegate content improvement to HealerAgent (improve_content mode)."""
        context = context or {}

        if not github_url:
            return self._error_response("Content improvement requires a GitHub URL.", sid)

        app_name = self._extract_project_name(github_url).replace('-', ' ').replace('_', ' ').title()

        # Extract live URL if present
        live_url = None
        live_match = re.search(r'https?://[^\s]+\.smartdevops\.site', text or '')
        if live_match:
            live_url = live_match.group(0)
        elif context.get('live_url'):
            live_url = context.get('live_url')

        # Extract description if present
        app_description = ''
        desc_match = re.search(r'(?:description|about)[:\s]+([^\n]+)', text or '', re.IGNORECASE)
        if desc_match:
            app_description = desc_match.group(1).strip()

        self.emit_log(f"   App name: {app_name}", "info", sid)
        if live_url:
            self.emit_log(f"   Live URL: {live_url}", "info", sid)
        if app_description:
            self.emit_log(f"   Description: {app_description}", "info", sid)

        return self.delegate_to_agent(
            self.agents['healer'],
            {
                'action': 'improve_content',
                'repo_url': github_url,
                'live_url': live_url,
                'app_name': app_name,
                'app_description': app_description,
            },
            {**context, 'sid': sid},
        )

    def _delegate_to_code_fixer(self, text, code_snippet, context, sid):
        context = context or {}
        if not code_snippet:
            code_snippet = self._extract_code_block(text)

        if not code_snippet:
            return self._error_response(
                "CodeFixer requires a code block.",
                sid,
            )

        return self.delegate_to_agent(
            self.agents['code_fixer'],
            {'action': 'fix_code', 'query': text, 'code': code_snippet},
            {**context, 'sid': sid},
        )

    def _delegate_to_error_recovery(self, text, github_url, context, sid):
        context = context or {}
        if not github_url:
            return self._error_response("ErrorRecovery requires a GitHub URL.", sid)
        self.emit_log("ErrorRecovery -> HealerAgent", "info", sid)
        return self._delegate_to_healer(text, context, sid)

    def _delegate_to_analyzer(self, text, github_url, context, sid):
        context = context or {}
        if not github_url:
            return self._error_response("Analyzer requires a GitHub URL.", sid)

        if 'analyzer' not in self.agents:
            return self._execute_general(text, context, sid)

        return self.delegate_to_agent(
            self.agents['analyzer'],
            {'action': 'analyze', 'repo_url': github_url},
            {**context, 'sid': sid},
        )

    # ============================================
    # DevOps Command Handler (API calls)
    # ============================================
    def _handle_devops_command(self, input_data, context, sid=None):
        context = context or {}
        action = input_data.get('action', '').lower()
        repo_url = input_data.get('repo_url') or context.get('repo_url')

        mode = input_data.get('mode', 'ci-cd+deploy')
        provider = input_data.get('provider') or input_data.get('deploy_method', 'self-host')

        self.emit_log(f"DevOps action: {action}", "info", sid)
        self.emit_log(f"Mode: {mode} | Provider: {provider}", "info", sid)

        if action == 'deploy':
            return self.delegate_to_agent(
                self.agents['deploy'],
                {
                    'action': 'deploy',
                    'repo_url': repo_url,
                    'project_name': self._extract_project_name(repo_url or ''),
                    'mode': mode if mode in ('self-deploy', 'custom-deploy') else 'self-deploy',
                    'provider': provider,
                    'deploy_method': provider,
                    'deploy_type': input_data.get('deploy_type', 'auto'),
                    'skip_pipeline': True,
                    'fullstack': input_data.get('deploy_type', 'auto') in ('auto', 'fullstack'),
                },
                {**context, 'sid': sid},
            )

        elif action == 'pipeline':
            return self.delegate_to_agent(
                self.agents['pipeline'],
                {
                    'action': 'create',
                    'repo_url': repo_url,
                    'mode': mode,
                    'deploy_method': provider,
                    'provider': provider,
                    'max_fix_attempts': input_data.get('max_fix_attempts', 50),
                    'auto_deploy': input_data.get(
                        'auto_deploy',
                        mode in ('ci-cd+deploy', 'self-deploy', 'custom-deploy')
                    ),
                    'run_pipeline': input_data.get(
                        'run_pipeline',
                        mode in ('ci-cd-only', 'ci-cd+deploy')
                    ),
                    'skip_pipeline': input_data.get(
                        'skip_pipeline',
                        mode in ('self-deploy', 'custom-deploy')
                    ),
                },
                {**context, 'sid': sid},
            )

        elif action in ('security', 'scan'):
            return self._delegate_to_security(
                f"security scan {repo_url or ''}", repo_url, context, sid
            )

        elif action == 'monitor':
            target_url = input_data.get('url')
            if target_url:
                return self.delegate_to_agent(
                    self.agents['monitor'],
                    {'action': 'check', 'urls': [target_url]},
                    {**context, 'sid': sid},
                )
            return self._delegate_to_monitor(input_data.get('url', ''), context, sid)

        elif action == 'scale':
            return self.delegate_to_agent(
                self.agents['scale'],
                {
                    'action': 'scale',
                    'repo_url': repo_url,
                    'service': input_data.get('service'),
                    'replicas': input_data.get('replicas', 3),
                },
                {**context, 'sid': sid},
            )

        elif action == 'improve_content':
            return self._delegate_to_improve_content(
                input_data.get('query', ''),
                repo_url,
                {**context, 'live_url': input_data.get('live_url'), 'app_name': input_data.get('app_name')},
                sid,
            )

        elif action in ('fix', 'fix_code'):
            if repo_url and 'github.com' in repo_url:
                return self.delegate_to_agent(
                    self.agents['code_fixer'],
                    {
                        'action': 'fix_repo',
                        'repo_url': repo_url,
                        'branch': input_data.get('branch'),
                    },
                    {**context, 'sid': sid},
                )
            code = input_data.get('code') or self._extract_code_block(
                input_data.get('error_message', '')
            )
            if code:
                return self._delegate_to_code_fixer(
                    input_data.get('error_message', ''), code, context, sid
                )
            return self._delegate_to_healer(
                input_data.get('error_message', ''), context, sid
            )

        elif action in ('analyze', 'review'):
            return self._delegate_to_analyzer('analyze', repo_url, context, sid)

        else:
            return self._execute_general(str(input_data), context, sid)

    # ============================================
    # Other Handlers
    # ============================================
    def _handle_file_upload(self, input_data, context, sid=None):
        context = context or {}
        self.emit_log("File upload received", "info", sid)
        files = input_data.get('files', [])
        return {
            'success': True,
            'type': 'file_upload',
            'status': 'received',
            'file_count': len(files),
            'response': f"Received {len(files)} file(s).",
        }

    def _handle_webhook(self, input_data, context, sid=None):
        context = context or {}
        self.emit_log("Webhook received", "info", sid)
        return {'success': True, 'type': 'webhook', 'status': 'received'}

    def _handle_general(self, input_data, context, sid=None):
        context = context or {}
        return self._execute_general(str(input_data), context, sid)

    def _execute_general(self, text, context, sid=None):
        context = context or {}
        response = self.think(text)

        if not response:
            response = (
                f"Received: '{text}'. I'm here to help with DevOps tasks - "
                f"try 'create pipeline for <github-url>', 'deploy <url>', "
                f"'scan <url>', 'monitor <url>', or paste code to 'fix'."
            )

        return {
            'success': True,
            'type': 'general',
            'status': 'completed',
            'response': response,
        }

    # ============================================
    # Helpers
    # ============================================
    def _extract_github_url(self, text):
        match = re.search(r'https?://github\.com/[\w\-\.]+/[\w\-\.]+', text)
        return match.group(0) if match else None

    def _extract_provider(self, text):
        text_lower = text.lower()
        for provider in ['vercel', 'render', 'railway', 'netlify', 'dockerhub', 'docker hub', 'fly']:
            if provider in text_lower:
                if 'docker' in provider:
                    return 'dockerhub'
                return provider
        return None

    def _extract_project_name(self, url):
        try:
            return url.rstrip('/').split('/')[-1]
        except Exception:
            return 'my-app'

    def _detect_error_in_text(self, text):
        error_keywords = ['error:', 'exception', 'failed:', 'traceback', 'stack trace']
        return any(k in text.lower() for k in error_keywords)

    def _extract_code_block(self, text):
        if not text:
            return None
        match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _looks_like_code_fix_request(self, text):
        if not text:
            return False
        text_lower = text.lower()
        fix_verbs = [
            'fix', 'debug', 'repair', 'optimize', 'refactor',
            'correct', 'improve', 'review this code',
        ]
        return any(v in text_lower for v in fix_verbs)

    def _error_response(self, message, sid=None):
        self.emit_log(f"{message}", "warning", sid)
        return {'success': False, 'error': message, 'response': message}

    # ============================================
    # Status
    # ============================================
    def get_execution_status(self, execution_id):
        return self.active_executions.get(execution_id)

    def get_all_executions(self):
        return list(self.active_executions.values())

    def get_agent_status(self):
        return {
            'orchestrator': self.to_dict(),
            'agents': {name: agent.to_dict() for name, agent in self.agents.items()},
        }