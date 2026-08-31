from .base_manager import BaseManager
from datetime import datetime


class NotificationManager(BaseManager):
    """Manager for notification operations"""
    
    def __init__(self, db):
        super().__init__(db, 'notifications')
    
    def create_notification(self, user_id, title, message, notification_type='info', link=None):
        """Create a notification"""
        notification_data = {
            'notification_id': self._generate_id('notif'),
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': notification_type,  # info, success, warning, error
            'link': link,
            'read': False,
            'created_at': datetime.now(),
            'read_at': None
        }
        
        return self.create(notification_data)
    
    def find_by_user(self, user_id, limit=50, skip=0, unread_only=False):
        """Find notifications by user"""
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = False
        
        return self.find_many(
            query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def mark_read(self, notification_id):
        """Mark notification as read"""
        return self.update(
            notification_id,
            {'read': True, 'read_at': datetime.now()},
            'notification_id'
        )
    
    def mark_all_read(self, user_id):
        """Mark all notifications as read"""
        result = self.collection.update_many(
            {'user_id': user_id, 'read': False},
            {'$set': {'read': True, 'read_at': datetime.now()}}
        )
        return result.modified_count
    
    def delete_notification(self, notification_id):
        """Delete notification"""
        return self.delete(notification_id, 'notification_id')
    
    def delete_all(self, user_id):
        """Delete all notifications for a user"""
        result = self.collection.delete_many({'user_id': user_id})
        return result.deleted_count
    
    def get_unread_count(self, user_id):
        """Get unread notification count"""
        return self.count({'user_id': user_id, 'read': False})
    
    def bulk_create(self, user_ids, title, message, notification_type='info'):
        """Create notifications for multiple users"""
        notifications = []
        for user_id in user_ids:
            notifications.append({
                'notification_id': self._generate_id('notif'),
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'link': None,
                'read': False,
                'created_at': datetime.now(),
                'read_at': None
            })
        
        return self.bulk_insert(notifications)