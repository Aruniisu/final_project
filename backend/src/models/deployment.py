from datetime import datetime
from bson import ObjectId
import uuid

class Deployment:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.deployments

    def create(self, user_id, project_id, environment='production', config=None):
        """Create a new deployment"""
        deployment_data = {
            'deployment_id': str(uuid.uuid4()),
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
        
        result = self.collection.insert_one(deployment_data)
        deployment_data['_id'] = str(result.inserted_id)
        return deployment_data

    def find_by_id(self, deployment_id):
        """Find deployment by ID"""
        try:
            deployment = self.collection.find_one({'deployment_id': deployment_id})
            if deployment:
                deployment['_id'] = str(deployment['_id'])
            return deployment
        except:
            return None

    def find_by_project(self, project_id, limit=50, offset=0):
        """Find deployments by project"""
        deployments = list(self.collection.find(
            {'project_id': project_id}
        ).skip(offset).limit(limit).sort('created_at', -1))
        
        for deployment in deployments:
            deployment['_id'] = str(deployment['_id'])
        return deployments

    def update_status(self, deployment_id, status, metrics=None):
        """Update deployment status"""
        update_data = {
            'status': status,
            'updated_at': datetime.now()
        }
        if status == 'running':
            update_data['started_at'] = datetime.now()
        if status in ['success', 'failed', 'cancelled']:
            update_data['completed_at'] = datetime.now()
            if self.find_by_id(deployment_id).get('started_at'):
                started = self.find_by_id(deployment_id)['started_at']
                update_data['duration'] = str(datetime.now() - started)
        if metrics:
            update_data['metrics'] = metrics
        
        result = self.collection.update_one(
            {'deployment_id': deployment_id},
            {'$set': update_data}
        )
        return result.modified_count > 0

    def add_log(self, deployment_id, log):
        """Add a log entry"""
        log['timestamp'] = datetime.now().isoformat()
        result = self.collection.update_one(
            {'deployment_id': deployment_id},
            {'$push': {'logs': log}}
        )
        return result.modified_count > 0