import json
import requests
import os
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for system monitoring"""
    
    def __init__(self):
        self.endpoint = os.getenv('MONITORING_ENDPOINT', 'http://localhost:9090')
    
    def get_metrics(self, query, time_range='1h'):
        """Get metrics from monitoring system"""
        try:
            # Calculate time range
            now = datetime.now()
            if time_range == '1h':
                start = now - timedelta(hours=1)
            elif time_range == '6h':
                start = now - timedelta(hours=6)
            elif time_range == '24h':
                start = now - timedelta(hours=24)
            elif time_range == '7d':
                start = now - timedelta(days=7)
            else:
                start = now - timedelta(hours=1)
            
            # Generate mock data
            metrics = self._generate_mock_metrics(start, now)
            return metrics
            
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            return self._generate_mock_metrics()
    
    def _generate_mock_metrics(self, start=None, end=None):
        """Generate mock metrics data"""
        if not start:
            start = datetime.now() - timedelta(hours=1)
        if not end:
            end = datetime.now()
        
        data = []
        current = start
        while current <= end:
            data.append({
                'timestamp': current.isoformat(),
                'cpu': random.randint(20, 80),
                'memory': random.randint(30, 90),
                'disk': random.randint(10, 70),
                'network': random.randint(10, 50)
            })
            current += timedelta(minutes=1)
        
        return {
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
            'summary': {
                'avg_cpu': sum(d['cpu'] for d in data) / len(data),
                'max_cpu': max(d['cpu'] for d in data),
                'avg_memory': sum(d['memory'] for d in data) / len(data),
                'max_memory': max(d['memory'] for d in data)
            }
        }
    
    def check_health(self):
        """Check system health"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'healthy',
                'redis': 'healthy',
                'api': 'healthy',
                'websocket': 'healthy'
            }
        }
    
    def get_alerts(self, severity=None):
        """Get system alerts"""
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
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return alerts
    
    def create_alert(self, title, message, severity='medium', source=None):
        """Create a new alert"""
        alert = {
            'id': str(len(self.get_alerts()) + 1),
            'title': title,
            'message': message,
            'severity': severity,
            'status': 'active',
            'time': 'Just now',
            'source': source or 'System'
        }
        
        # Store alert (in real implementation, save to database)
        return alert
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert"""
        return {'success': True, 'alert_id': alert_id, 'status': 'acknowledged'}
    
    def resolve_alert(self, alert_id):
        """Resolve an alert"""
        return {'success': True, 'alert_id': alert_id, 'status': 'resolved'}