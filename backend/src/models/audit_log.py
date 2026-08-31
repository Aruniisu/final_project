from datetime import datetime
from bson import ObjectId

class AuditLog:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.audit_logs

    def create(self, user_id, action, details=None):
        """Create audit log entry"""
        log_data = {
            'user_id': user_id,
            'action': action,
            'details': details or {},
            'timestamp': datetime.now(),
            'ip': details.get('ip', ''),
            'user_agent': details.get('user_agent', '')
        }
        
        result = self.collection.insert_one(log_data)
        log_data['_id'] = str(result.inserted_id)
        return log_data

    def find_by_user(self, user_id, limit=100, offset=0):
        """Find logs by user"""
        logs = list(self.collection.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).skip(offset).limit(limit))
        
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs

    def find_by_action(self, action, limit=100, offset=0):
        """Find logs by action"""
        logs = list(self.collection.find(
            {'action': action}
        ).sort('timestamp', -1).skip(offset).limit(limit))
        
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs

    def get_recent(self, limit=100):
        """Get recent logs"""
        logs = list(self.collection.find().sort('timestamp', -1).limit(limit))
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs