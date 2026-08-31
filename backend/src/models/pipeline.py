from datetime import datetime
from bson import ObjectId
import uuid

class Pipeline:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.pipelines

    def create(self, user_id, name, repo, branch='main', config=None):
        """Create a new pipeline"""
        pipeline_data = {
            'pipeline_id': str(uuid.uuid4()),
            'user_id': user_id,
            'name': name,
            'repo': repo,
            'branch': branch,
            'status': 'pending',
            'progress': 0,
            'config': config or {},
            'steps': [],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'duration': None
        }
        
        result = self.collection.insert_one(pipeline_data)
        pipeline_data['_id'] = str(result.inserted_id)
        return pipeline_data

    def find_by_id(self, pipeline_id):
        """Find pipeline by ID"""
        try:
            pipeline = self.collection.find_one({'pipeline_id': pipeline_id})
            if pipeline:
                pipeline['_id'] = str(pipeline['_id'])
            return pipeline
        except:
            return None

    def find_by_user(self, user_id, limit=50, offset=0):
        """Find pipelines by user"""
        pipelines = list(self.collection.find(
            {'user_id': user_id}
        ).skip(offset).limit(limit).sort('created_at', -1))
        
        for pipeline in pipelines:
            pipeline['_id'] = str(pipeline['_id'])
        return pipelines

    def update_status(self, pipeline_id, status, progress=None):
        """Update pipeline status"""
        update_data = {
            'status': status,
            'updated_at': datetime.now()
        }
        if progress is not None:
            update_data['progress'] = progress
        if status == 'running' and not self.find_by_id(pipeline_id).get('started_at'):
            update_data['started_at'] = datetime.now()
        if status in ['success', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.now()
            if self.find_by_id(pipeline_id).get('started_at'):
                started = self.find_by_id(pipeline_id)['started_at']
                update_data['duration'] = str(datetime.now() - started)
        
        result = self.collection.update_one(
            {'pipeline_id': pipeline_id},
            {'$set': update_data}
        )
        return result.modified_count > 0

    def add_step(self, pipeline_id, step):
        """Add a step to pipeline"""
        step['id'] = str(uuid.uuid4())
        step['status'] = 'pending'
        step['started_at'] = None
        step['completed_at'] = None
        
        result = self.collection.update_one(
            {'pipeline_id': pipeline_id},
            {'$push': {'steps': step}}
        )
        return result.modified_count > 0

    def update_step(self, pipeline_id, step_id, data):
        """Update a pipeline step"""
        result = self.collection.update_one(
            {'pipeline_id': pipeline_id, 'steps.id': step_id},
            {'$set': {f'steps.$.{k}': v for k, v in data.items()}}
        )
        return result.modified_count > 0

    def add_log(self, pipeline_id, log):
        """Add a log entry to pipeline"""
        log['timestamp'] = datetime.now().isoformat()
        result = self.collection.update_one(
            {'pipeline_id': pipeline_id},
            {'$push': {'logs': log}}
        )
        return result.modified_count > 0

    def delete(self, pipeline_id):
        """Delete pipeline"""
        result = self.collection.delete_one({'pipeline_id': pipeline_id})
        return result.deleted_count > 0