"""
Monitoring API — Real-time monitoring endpoints
================================================
"""

import os
import time
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify

monitoring_bp = Blueprint('monitoring', __name__)


# ============================================
# 📊 METRICS — Real data from monitor_service
# ============================================
@monitoring_bp.route('/metrics', methods=['GET', 'OPTIONS'])
def get_metrics():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service

        stats = monitor_service.get_stats()

        return jsonify({
            'success': True,
            'metrics': {
                'uptime': f"{stats.get('avg_uptime', 100):.2f}%",
                'requests': f"{stats.get('total_checks', 0)}",
                'errors': stats.get('total_errors', 0),
                'latency': f"{stats.get('avg_latency', 0)}ms",
                'active_monitors': stats.get('active_monitors', 0),
                'total_monitors': stats.get('total_monitors', 0),
            },
            'monitors': stats.get('monitors', []),
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📈 HEALTH — System health
# ============================================
@monitoring_bp.route('/health', methods=['GET', 'OPTIONS'])
def get_health():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service
        from services.scale_service import scale_service

        monitor_stats = monitor_service.get_stats()
        scale_stats = scale_service.get_stats()

        # Count services
        monitors = monitor_stats.get('monitors', [])
        healthy = sum(1 for m in monitors if m.get('uptime_percent', 0) >= 99)
        warning = sum(1 for m in monitors if 80 <= m.get('uptime_percent', 0) < 99)
        critical = sum(1 for m in monitors if m.get('uptime_percent', 0) < 80)

        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'total': len(monitors),
                'healthy': healthy,
                'warning': warning,
                'critical': critical,
            },
            'infrastructure': {
                'total_services': scale_stats.get('total_services', 0),
                'total_replicas': scale_stats.get('total_replicas', 0),
                'avg_cpu': scale_stats.get('avg_cpu', 0),
                'avg_memory': scale_stats.get('avg_memory', 0),
            },
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 🔔 ALERTS
# ============================================
@monitoring_bp.route('/alerts', methods=['GET', 'OPTIONS'])
def get_alerts():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service

        alerts = []
        monitors = monitor_service.list_monitors()

        for m in monitors:
            uptime = m.get('uptime_percent', 100)
            url = m.get('url', '')

            if uptime < 80:
                alerts.append({
                    'id': f"alert-{m.get('id')}-critical",
                    'severity': 'critical',
                    'message': f"Critical: {url} uptime {uptime}%",
                    'monitor_id': m.get('id'),
                    'url': url,
                    'uptime': uptime,
                    'created_at': m.get('last_check_at') or time.time(),
                })
            elif uptime < 99:
                alerts.append({
                    'id': f"alert-{m.get('id')}-warning",
                    'severity': 'warning',
                    'message': f"Warning: {url} uptime {uptime}%",
                    'monitor_id': m.get('id'),
                    'url': url,
                    'uptime': uptime,
                    'created_at': m.get('last_check_at') or time.time(),
                })

        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ✅ ACKNOWLEDGE ALERT
# ============================================
@monitoring_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST', 'OPTIONS'])
def acknowledge_alert(alert_id):
    if request.method == 'OPTIONS':
        return '', 204

    # Simple no-op for now
    return jsonify({'success': True, 'status': 'acknowledged', 'alert_id': alert_id})


# ============================================
# 📊 MONITORS — List / Get / Start / Stop
# ============================================
@monitoring_bp.route('/monitors', methods=['GET', 'OPTIONS'])
def list_monitors():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service
        return jsonify({
            'success': True,
            'monitors': monitor_service.list_monitors(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_bp.route('/monitors/<monitor_id>', methods=['GET', 'OPTIONS'])
def get_monitor(monitor_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service
        m = monitor_service.get_monitor(monitor_id)
        if not m:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'monitor': m})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_bp.route('/monitors/<monitor_id>', methods=['DELETE', 'OPTIONS'])
def delete_monitor(monitor_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service
        ok = monitor_service.delete_monitor(monitor_id)
        return jsonify({'success': ok})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_bp.route('/monitors/<monitor_id>/stop', methods=['POST', 'OPTIONS'])
def stop_monitor(monitor_id):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.monitor_service import monitor_service
        ok = monitor_service.stop_monitor(monitor_id)
        return jsonify({'success': ok})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 📈 INFRASTRUCTURE — Scale stats
# ============================================
@monitoring_bp.route('/infrastructure', methods=['GET', 'OPTIONS'])
def get_infrastructure():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.scale_service import scale_service
        return jsonify({
            'success': True,
            'infrastructure': scale_service.get_stats(),
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@monitoring_bp.route('/infrastructure/<service_name>', methods=['GET', 'OPTIONS'])
def get_service(service_name):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from services.scale_service import scale_service
        s = scale_service.get_service(service_name)
        if not s:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify({'success': True, 'service': s})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500