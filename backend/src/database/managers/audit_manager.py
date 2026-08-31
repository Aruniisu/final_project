from .base_manager import BaseManager
from datetime import datetime


class AuditManager(BaseManager):
    """Manager for audit log operations"""
    
    def __init__(self, db):
        super().__init__(db, 'audit_logs')
    
    def log_action(self, user_id, action, details=None, ip=None, user_agent=None):
        """Log an action"""
        log_data = {
            'user_id': user_id,
            'action': action,
            'details': details or {},
            'ip': ip or '',
            'user_agent': user_agent or '',
            'timestamp': datetime.now()
        }
        
        return self.create(log_data)
    
    def find_by_user(self, user_id, limit=100, skip=0):
        """Find logs by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('timestamp', -1)],
            limit=limit,
            skip=skip
        )
    
    def find_by_action(self, action, limit=100, skip=0):
        """Find logs by action"""
        return self.find_many(
            {'action': action},
            sort=[('timestamp', -1)],
            limit=limit,
            skip=skip
        )
    
    def find_by_date_range(self, start_date, end_date, limit=100, skip=0):
        """Find logs by date range"""
        query = {
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        return self.find_many(
            query,
            sort=[('timestamp', -1)],
            limit=limit,
            skip=skip
        )
    
    def get_recent_logs(self, limit=100):
        """Get recent logs"""
        return self.find_many(
            {},
            sort=[('timestamp', -1)],
            limit=limit
        )
    
    def get_user_activity(self, user_id, days=7):
        """Get user activity for a period"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        return self.find_many({
            'user_id': user_id,
            'timestamp': {'$gte': start_date}
        }, sort=[('timestamp', -1)])
    
    def get_activity_summary(self, days=7):
        """Get activity summary"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        # Total actions
        total = self.count({'timestamp': {'$gte': start_date}})
        
        # By action type
        by_action = self.aggregate([
            {'$match': {'timestamp': {'$gte': start_date}}},
            {'$group': {'_id': '$action', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # By user
        by_user = self.aggregate([
            {'$match': {'timestamp': {'$gte': start_date}}},
            {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        return {
            'total_actions': total,
            'by_action': {item['_id']: item['count'] for item in by_action},
            'top_users': [{'user_id': item['_id'], 'count': item['count']} for item in by_user],
            'period_days': days
        }