from datetime import datetime
from bson import ObjectId
import uuid

class Training:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.trainings

    def create(self, user_id, name, model_type, config=None):
        """Create a new training job"""
        training_data = {
            'training_id': str(uuid.uuid4()),
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
        
        result = self.collection.insert_one(training_data)
        training_data['_id'] = str(result.inserted_id)
        return training_data

    def find_by_id(self, training_id):
        """Find training by ID"""
        try:
            training = self.collection.find_one({'training_id': training_id})
            if training:
                training['_id'] = str(training['_id'])
            return training
        except:
            return None

    def find_by_user(self, user_id, limit=50, offset=0):
        """Find trainings by user"""
        trainings = list(self.collection.find(
            {'user_id': user_id}
        ).skip(offset).limit(limit).sort('created_at', -1))
        
        for training in trainings:
            training['_id'] = str(training['_id'])
        return trainings

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
            if self.find_by_id(training_id).get('started_at'):
                started = self.find_by_id(training_id)['started_at']
                update_data['duration'] = str(datetime.now() - started)
        if metrics:
            update_data['metrics'] = metrics
        
        result = self.collection.update_one(
            {'training_id': training_id},
            {'$set': update_data}
        )
        return result.modified_count > 0

    def add_log(self, training_id, log):
        """Add a log entry"""
        log['timestamp'] = datetime.now().isoformat()
        result = self.collection.update_one(
            {'training_id': training_id},
            {'$push': {'logs': log}}
        )
        return result.modified_count > 0