from datetime import datetime
from bson import ObjectId
import uuid

class Project:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.projects

    def create(self, user_id, name, description=None, type='web'):
        """Create a new project"""
        project_data = {
            'project_id': str(uuid.uuid4()),
            'user_id': user_id,
            'name': name,
            'description': description,
            'type': type,
            'status': 'created',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'metadata': {},
            'settings': {
                'auto_deploy': False,
                'branch': 'main',
                'environment': 'development'
            }
        }
        
        result = self.collection.insert_one(project_data)
        project_data['_id'] = str(result.inserted_id)
        return project_data

    def find_by_id(self, project_id):
        """Find project by ID"""
        try:
            project = self.collection.find_one({'project_id': project_id})
            if project:
                project['_id'] = str(project['_id'])
            return project
        except:
            return None

    def find_by_user(self, user_id, limit=50, offset=0):
        """Find projects by user"""
        projects = list(self.collection.find(
            {'user_id': user_id}
        ).skip(offset).limit(limit).sort('created_at', -1))
        
        for project in projects:
            project['_id'] = str(project['_id'])
        return projects

    def update(self, project_id, data):
        """Update project"""
        data['updated_at'] = datetime.now()
        result = self.collection.update_one(
            {'project_id': project_id},
            {'$set': data}
        )
        return result.modified_count > 0

    def delete(self, project_id):
        """Delete project"""
        result = self.collection.delete_one({'project_id': project_id})
        return result.deleted_count > 0

    def get_all(self, limit=50, offset=0):
        """Get all projects"""
        projects = list(self.collection.find().skip(offset).limit(limit).sort('created_at', -1))
        for project in projects:
            project['_id'] = str(project['_id'])
        return projects