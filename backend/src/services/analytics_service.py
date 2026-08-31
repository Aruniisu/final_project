from datetime import datetime, timedelta
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for system analytics"""
    
    def __init__(self, mongo):
        self.mongo = mongo
    
    def get_deployment_stats(self, days=7):
        """Get deployment statistics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get deployments from database
            deployments = list(self.mongo.db.deployments.find({
                'created_at': {'$gte': start_date}
            }))
            
            # Calculate stats
            total = len(deployments)
            successful = sum(1 for d in deployments if d.get('status') == 'success')
            failed = sum(1 for d in deployments if d.get('status') == 'failed')
            in_progress = sum(1 for d in deployments if d.get('status') == 'running')
            
            # Deployment frequency
            daily = {}
            for d in deployments:
                date = d['created_at'].strftime('%Y-%m-%d')
                daily[date] = daily.get(date, 0) + 1
            
            # Success rate
            success_rate = (successful / total * 100) if total > 0 else 0
            
            return {
                'total_deployments': total,
                'successful': successful,
                'failed': failed,
                'in_progress': in_progress,
                'success_rate': round(success_rate, 2),
                'daily': daily,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting deployment stats: {e}")
            return None
    
    def get_pipeline_stats(self, days=7):
        """Get pipeline statistics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            pipelines = list(self.mongo.db.pipelines.find({
                'created_at': {'$gte': start_date}
            }))
            
            total = len(pipelines)
            successful = sum(1 for p in pipelines if p.get('status') == 'success')
            failed = sum(1 for p in pipelines if p.get('status') == 'failed')
            running = sum(1 for p in pipelines if p.get('status') == 'running')
            
            # Average duration
            durations = []
            for p in pipelines:
                if p.get('duration'):
                    try:
                        # Parse duration string
                        duration_str = p['duration']
                        if ':' in duration_str:
                            parts = duration_str.split(':')
                            if len(parts) == 3:
                                hours, minutes, seconds = map(float, parts)
                                durations.append(hours * 3600 + minutes * 60 + seconds)
                    except:
                        pass
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_pipelines': total,
                'successful': successful,
                'failed': failed,
                'running': running,
                'avg_duration_seconds': round(avg_duration, 2),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return None
    
    def get_user_activity(self, days=7):
        """Get user activity statistics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get audit logs
            logs = list(self.mongo.db.audit_logs.find({
                'timestamp': {'$gte': start_date}
            }))
            
            # User activity
            user_activity = Counter(log.get('user_id', 'anonymous') for log in logs)
            
            # Action types
            action_counts = Counter(log.get('action', 'unknown') for log in logs)
            
            return {
                'total_actions': len(logs),
                'active_users': len(user_activity),
                'user_activity': dict(user_activity.most_common(10)),
                'action_counts': dict(action_counts.most_common(10)),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return None
    
    def get_system_metrics(self, days=7):
        """Get system metrics"""
        try:
            # Get system metrics from database
            metrics = list(self.mongo.db.system_metrics.find({
                'timestamp': {'$gte': datetime.now() - timedelta(days=days)}
            }).sort('timestamp', -1).limit(100))
            
            if not metrics:
                return {
                    'avg_cpu': 0,
                    'avg_memory': 0,
                    'avg_disk': 0,
                    'uptime': '99.9%',
                    'period_days': days
                }
            
            avg_cpu = sum(m.get('cpu', 0) for m in metrics) / len(metrics)
            avg_memory = sum(m.get('memory', 0) for m in metrics) / len(metrics)
            avg_disk = sum(m.get('disk', 0) for m in metrics) / len(metrics)
            
            return {
                'avg_cpu': round(avg_cpu, 2),
                'avg_memory': round(avg_memory, 2),
                'avg_disk': round(avg_disk, 2),
                'uptime': '99.9%',
                'period_days': days,
                'data_points': len(metrics)
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def get_analytics_dashboard(self, days=7):
        """Get complete analytics dashboard"""
        return {
            'deployments': self.get_deployment_stats(days),
            'pipelines': self.get_pipeline_stats(days),
            'user_activity': self.get_user_activity(days),
            'system_metrics': self.get_system_metrics(days),
            'generated_at': datetime.now().isoformat()
        }