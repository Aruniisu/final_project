from .base_manager import BaseManager
from datetime import datetime


class TrainingManager(BaseManager):
    """Manager for training operations"""
    
    def __init__(self, db):
        super().__init__(db, 'trainings')
    
    def create_training(self, user_id, name, model_type, config=None):
        """Create a new training job"""
        training_data = {
            'training_id': self._generate_id('train'),
            'user_id': user_id,
            'name': name,
            'model_type': model_type,
            'status': 'pending',
            'progress': 0,
            'config': config or {},
            'metrics': {},
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'duration': None,
            'logs': []
        }
        
        return self.create(training_data)
    
    def find_by_training_id(self, training_id):
        """Find training by training_id"""
        return self.find_by_id(training_id, 'training_id')
    
    def find_by_user(self, user_id, limit=50, skip=0):
        """Find trainings by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def update_status(self, training_id, status, progress=None, metrics=None):
        """Update training status"""
        update_data = {
            'status': status,
            'updated_at': datetime.now()
        }
        
        if progress is not None:
            update_data['progress'] = progress
        
        if status == 'running':
            update_data['started_at'] = datetime.now()
        
        if status in ['completed', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.now()
            training = self.find_by_training_id(training_id)
            if training and training.get('started_at'):
                duration = datetime.now() - training['started_at']
                update_data['duration'] = str(duration)
        
        if metrics:
            update_data['metrics'] = metrics
        
        return self.update(training_id, update_data, 'training_id')
    
    def add_log(self, training_id, level, message):
        """Add a log entry"""
        log = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        return self.collection.update_one(
            {'training_id': training_id},
            {'$push': {'logs': log}}
        ).modified_count > 0
    
    def delete_training(self, training_id):
        """Delete training"""
        return self.delete(training_id, 'training_id')
    
    def get_training_stats(self, user_id=None):
        """Get training statistics"""
        query = {'user_id': user_id} if user_id else {}
        
        total = self.count(query)
        by_status = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ])
        
        return {
            'total_trainings': total,
            'by_status': {item['_id']: item['count'] for item in by_status}
        }