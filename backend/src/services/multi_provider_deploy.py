"""
MultiProviderDeployService — Wrapper for UniversalDeployer
============================================================
Thin wrapper — delegates to UniversalDeployer.
"""

import os
from typing import Dict, Any, Optional


class MultiProviderDeployService:
    """Wrapper — delegates to UniversalDeployer."""

    def __init__(self, agent=None):
        self.agent = agent

        try:
            from .universal_deployer import UniversalDeployer
        except ImportError:
            from src.services.universal_deployer import UniversalDeployer

        self._deployer = UniversalDeployer(agent=agent)

    def deploy(
        self,
        provider: str,
        owner: str,
        repo: str,
        repo_url: str,
        default_branch: str,
        stack_info: Dict,
        sid: Optional[str] = None,
        on_log=None,
    ) -> Dict:
        """Delegate to UniversalDeployer."""
        return self._deployer.deploy(
            provider=provider,
            owner=owner,
            repo=repo,
            repo_url=repo_url,
            default_branch=default_branch,
            stack_info=stack_info,
            sid=sid,
            on_log=on_log,
        )