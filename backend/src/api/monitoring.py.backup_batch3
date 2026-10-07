from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import random
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get monitoring metrics - FIXED"""
    time_range = request.args.get('timeRange', '1h')
    
    # Generate mock metrics data
    now = datetime.now()
    data = []
    
    points = {'1h': 60, '6h': 360, '24h': 1440, '7d': 10080, '30d': 43200}.get(time_range, 60)
    
    for i in range(min(points, 100)):
        timestamp = now - timedelta(minutes=points - i)
        data.append({
            'timestamp': timestamp.isoformat(),
            'cpu': random.randint(20, 80),
            'memory': random.randint(30, 90),
            'disk': random.randint(10, 70),
            'latency': random.randint(50, 300)
        })
    
    return jsonify({
        'metrics': {
            'uptime': '99.92%',
            'requests': f"{random.randint(10, 15)}.4k",
            'errors': random.randint(30, 60),
            'latency': f"{random.randint(150, 300)}ms",
            'cpu': random.randint(20, 80),
            'memory': random.randint(30, 90),
            'disk': random.randint(10, 70)
        },
        'history': data,
        'time_range': time_range
    }), 200


@monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts - FIXED"""
    status = request.args.get('status', 'all')
    
    alerts = [
        {
            'id': '1',
            'title': 'High CPU Usage Detected',
            'message': 'CPU usage exceeded 85% threshold on Production Cluster',
            'severity': 'critical',
            'status': 'active',
            'time': '2 minutes ago',
            'source': 'Production Cluster'
        },
        {
            'id': '2',
            'title': 'Database Connection Timeout',
            'message': 'Multiple connection timeouts detected from API service',
            'severity': 'high',
            'status': 'acknowledged',
            'time': '15 minutes ago',
            'source': 'PostgreSQL'
        },
        {
            'id': '3',
            'title': 'Memory Usage Warning',
            'message': 'Memory usage approaching 80% on Staging Cluster',
            'severity': 'medium',
            'status': 'active',
            'time': '45 minutes ago',
            'source': 'Staging Cluster'
        }
    ]
    
    if status != 'all':
        alerts = [a for a in alerts if a['status'] == status or a['severity'] == status]
    
    return jsonify(alerts), 200


@monitoring_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert - FIXED"""
    return jsonify({
        'success': True,
        'message': f'Alert {alert_id} acknowledged',
        'alert_id': alert_id,
        'status': 'acknowledged'
    }), 200


@monitoring_bp.route('/health', methods=['GET'])
def get_health():
    """Get system health - FIXED"""
    return jsonify({
        'status': 'healthy',
        'services': 12,
        'uptime': '99.9%',
        'timestamp': datetime.now().isoformat()
    }), 200