from .base_manager import BaseManager
from datetime import datetime


class PipelineManager(BaseManager):
    """Manager for pipeline operations"""
    
    def __init__(self, db):
        super().__init__(db, 'pipelines')
    
    def create_pipeline(self, user_id, name, repo, branch='main', config=None):
        """Create a new pipeline"""
        pipeline_data = {
            'pipeline_id': self._generate_id('pipe'),
            'user_id': user_id,
            'name': name,
            'repo': repo,
            'branch': branch,
            'status': 'pending',
            'progress': 0,
            'config': config or {},
            'steps': [],
            'logs': [],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'duration': None
        }
        
        return self.create(pipeline_data)
    
    def find_by_pipeline_id(self, pipeline_id):
        """Find pipeline by pipeline_id"""
        return self.find_by_id(pipeline_id, 'pipeline_id')
    
    def find_by_user(self, user_id, limit=50, skip=0):
        """Find pipelines by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def update_status(self, pipeline_id, status, progress=None):
        """Update pipeline status"""
        update_data = {'status': status, 'updated_at': datetime.now()}
        
        if progress is not None:
            update_data['progress'] = progress
        
        if status == 'running' and not self.find_by_pipeline_id(pipeline_id).get('started_at'):
            update_data['started_at'] = datetime.now()
        
        if status in ['success', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.now()
            pipeline = self.find_by_pipeline_id(pipeline_id)
            if pipeline and pipeline.get('started_at'):
                duration = datetime.now() - pipeline['started_at']
                update_data['duration'] = str(duration)
        
        return self.update(pipeline_id, update_data, 'pipeline_id')
    
    def add_step(self, pipeline_id, step):
        """Add a step to pipeline"""
        step['id'] = self._generate_id('step')
        step['status'] = 'pending'
        step['started_at'] = None
        step['completed_at'] = None
        
        return self.collection.update_one(
            {'pipeline_id': pipeline_id},
            {'$push': {'steps': step}}
        ).modified_count > 0
    
    def update_step(self, pipeline_id, step_id, data):
        """Update a pipeline step"""
        return self.collection.update_one(
            {'pipeline_id': pipeline_id, 'steps.id': step_id},
            {'$set': {f'steps.$.{k}': v for k, v in data.items()}}
        ).modified_count > 0
    
    def add_log(self, pipeline_id, level, message):
        """Add a log entry"""
        log = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        return self.collection.update_one(
            {'pipeline_id': pipeline_id},
            {'$push': {'logs': log}}
        ).modified_count > 0
    
    def delete_pipeline(self, pipeline_id):
        """Delete pipeline"""
        return self.delete(pipeline_id, 'pipeline_id')
    
    def get_pipeline_stats(self, user_id=None):
        """Get pipeline statistics"""
        query = {'user_id': user_id} if user_id else {}
        
        total = self.count(query)
        by_status = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ])
        
        # Average duration
        avg_duration = self.aggregate([
            {'$match': {'status': 'success', 'duration': {'$exists': True}}},
            {'$group': {'_id': None, 'avg_duration': {'$avg': '$duration'}}}
        ])
        
        return {
            'total_pipelines': total,
            'by_status': {item['_id']: item['count'] for item in by_status},
            'avg_duration': avg_duration[0]['avg_duration'] if avg_duration else None
        }