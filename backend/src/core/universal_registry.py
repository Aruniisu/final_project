"""
Universal App Registry — Single Source of Truth
================================================
Aggregates apps from ALL sources (ProcessManager + SelfHostService).
"""

from core.process_manager import manager as process_manager

_self_host_service = None


def set_self_host_service(service):
    """Link SelfHostService (called after Orchestrator init)."""
    global _self_host_service
    _self_host_service = service
    print("✅ Universal Registry → SelfHostService linked")


def _normalize_status(s: str) -> str:
    s = str(s).lower()
    if s in ('running', 'live', 'healthy', 'deployed', 'success', 'ready'):
        return 'running'
    if s in ('crashed', 'failed', 'error', 'dead', 'fail'):
        return 'crashed'
    if s in ('stopped', 'stopping', 'inactive'):
        return 'stopped'
    return 'unknown'


def _extract_host(url: str) -> str:
    """Extract hostname from URL for display name fallback."""
    if not url:
        return ''
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ''
        # Strip common prefixes for cleaner display
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def _get_self_host_apps() -> list:
    """Extract apps from SelfHostService (Cloudflare tunnels)."""
    if not _self_host_service:
        return []

    out = []
    try:
        deployments = None
        for method in ['list_deployments', 'get_deployments', 'list_all',
                       'get_all', 'list_active']:
            if hasattr(_self_host_service, method):
                try:
                    deployments = getattr(_self_host_service, method)()
                    break
                except Exception:
                    pass

        if not deployments and hasattr(_self_host_service, 'deployments'):
            deployments = _self_host_service.deployments

        if not deployments:
            return []

        if isinstance(deployments, dict):
            deployments = list(deployments.values())

        for idx, d in enumerate(deployments):
            if not isinstance(d, dict):
                continue

            url = d.get('url') or d.get('live_url') or ''
            host = _extract_host(url)

            # ⭐ Better name fallback: name → project_name → deploy_id → hostname → tunnel-N
            name = (d.get('name')
                    or d.get('project_name')
                    or d.get('deploy_id')
                    or host
                    or f'tunnel-{idx + 1}')

            out.append({
                'service_name': name,
                'display_name': name,
                'status': _normalize_status(d.get('status', 'unknown')),
                'port': d.get('port', 0),
                'url': url or None,
                'pid': d.get('pid', 0),
                'cpu_percent': d.get('cpu_percent', 0),
                'memory_percent': d.get('memory_percent', 0),
                'memory_mb': d.get('memory_mb', 0),
                'crashes': 0,
                'uptime_seconds': d.get('uptime', 0),
                'replicas': 1,
                'requests_per_sec': 0,
                'path': d.get('path', ''),
                'command': d.get('command', ''),
                'id': d.get('deploy_id') or d.get('id') or f'selfhost-{idx}',
                'image': 'self-host-tunnel',
                'source': 'self-host',
                'managed_by': 'infra-agent',
            })
    except Exception as e:
        print(f"⚠️  SelfHost extraction: {e}")
    return out


def list_all_apps() -> list:
    """Get ALL apps from ALL sources."""
    apps = []

    # 1. ProcessManager (apps launched via infra agent)
    try:
        for a in process_manager.list_apps():
            a['source'] = a.get('source', 'process-manager')
            a['managed_by'] = 'infra-agent'
            apps.append(a)
    except Exception as e:
        print(f"⚠️  ProcessManager: {e}")

    # 2. SelfHostService (Cloudflare tunnels — deploy/page launches)
    try:
        apps.extend(_get_self_host_apps())
    except Exception as e:
        print(f"⚠️  SelfHost: {e}")

    return apps


def find_app(name: str):
    """Find app by name across all sources."""
    for a in list_all_apps():
        if a.get('service_name') == name or a.get('id') == name:
            return a
    return None


def get_stats() -> dict:
    """Aggregate stats from all sources."""
    apps = list_all_apps()
    return {
        'total': len(apps),
        'running': len([a for a in apps if a['status'] == 'running']),
        'crashed': len([a for a in apps if a['status'] == 'crashed']),
        'stopped': len([a for a in apps if a['status'] == 'stopped']),
        'by_source': {
            'process-manager': len([a for a in apps if a['source'] == 'process-manager']),
            'self-host': len([a for a in apps if a['source'] == 'self-host']),
        },
    }