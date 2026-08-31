from .base_manager import BaseManager
from datetime import datetime


class DeploymentManager(BaseManager):
    """Manager for deployment operations"""
    
    def __init__(self, db):
        super().__init__(db, 'deployments')
    
    def create_deployment(self, user_id, project_id, environment='production', config=None):
        """Create a new deployment"""
        deployment_data = {
            'deployment_id': self._generate_id('dep'),
            'user_id': user_id,
            'project_id': project_id,
            'environment': environment,
            'status': 'pending',
            'config': config or {},
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'duration': None,
            'logs': [],
            'metrics': {}
        }
        
        return self.create(deployment_data)
    
    def find_by_deployment_id(self, deployment_id):
        """Find deployment by deployment_id"""
        return self.find_by_id(deployment_id, 'deployment_id')
    
    def find_by_project(self, project_id, limit=50, skip=0):
        """Find deployments by project"""
        return self.find_many(
            {'project_id': project_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def find_by_user(self, user_id, limit=50, skip=0):
        """Find deployments by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def update_status(self, deployment_id, status, metrics=None):
        """Update deployment status"""
        update_data = {'status': status, 'updated_at': datetime.now()}
        
        if status == 'running':
            update_data['started_at'] = datetime.now()
        
        if status in ['success', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.now()
            deployment = self.find_by_deployment_id(deployment_id)
            if deployment and deployment.get('started_at'):
                duration = datetime.now() - deployment['started_at']
                update_data['duration'] = str(duration)
        
        if metrics:
            update_data['metrics'] = metrics
        
        return self.update(deployment_id, update_data, 'deployment_id')
    
    def add_log(self, deployment_id, level, message):
        """Add a log entry"""
        log = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        return self.collection.update_one(
            {'deployment_id': deployment_id},
            {'$push': {'logs': log}}
        ).modified_count > 0
    
    def delete_deployment(self, deployment_id):
        """Delete deployment"""
        return self.delete(deployment_id, 'deployment_id')
    
    def get_deployment_stats(self, user_id=None):
        """Get deployment statistics"""
        query = {'user_id': user_id} if user_id else {}
        
        total = self.count(query)
        by_status = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ])
        
        by_environment = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$environment', 'count': {'$sum': 1}}}
        ])
        
        return {
            'total_deployments': total,
            'by_status': {item['_id']: item['count'] for item in by_status},
            'by_environment': {item['_id']: item['count'] for item in by_environment}
        }