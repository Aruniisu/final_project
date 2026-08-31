from datetime import datetime
from bson import ObjectId
import uuid

class Notification:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.notifications

    def create(self, user_id, title, message, type='info', link=None):
        """Create notification"""
        notification_data = {
            'notification_id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': type,  # info, success, warning, error
            'link': link,
            'read': False,
            'created_at': datetime.now(),
            'read_at': None
        }
        
        result = self.collection.insert_one(notification_data)
        notification_data['_id'] = str(result.inserted_id)
        return notification_data

    def find_by_user(self, user_id, limit=50, offset=0):
        """Find notifications by user"""
        notifications = list(self.collection.find(
            {'user_id': user_id}
        ).sort('created_at', -1).skip(offset).limit(limit))
        
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
        return notifications

    def mark_read(self, notification_id):
        """Mark notification as read"""
        result = self.collection.update_one(
            {'notification_id': notification_id},
            {'$set': {'read': True, 'read_at': datetime.now()}}
        )
        return result.modified_count > 0

    def mark_all_read(self, user_id):
        """Mark all notifications as read"""
        result = self.collection.update_many(
            {'user_id': user_id, 'read': False},
            {'$set': {'read': True, 'read_at': datetime.now()}}
        )
        return result.modified_count

    def delete(self, notification_id):
        """Delete notification"""
        result = self.collection.delete_one({'notification_id': notification_id})
        return result.deleted_count > 0

    def get_unread_count(self, user_id):
        """Get unread notification count"""
        return self.collection.count_documents({'user_id': user_id, 'read': False})