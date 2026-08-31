from .base_manager import BaseManager
from datetime import datetime


class ProjectManager(BaseManager):
    """Manager for project operations"""
    
    def __init__(self, db):
        super().__init__(db, 'projects')
    
    def create_project(self, user_id, name, description=None, project_type='web'):
        """Create a new project"""
        project_data = {
            'project_id': self._generate_id('proj'),
            'user_id': user_id,
            'name': name,
            'description': description,
            'type': project_type,
            'status': 'created',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'metadata': {},
            'settings': {
                'auto_deploy': False,
                'branch': 'main',
                'environment': 'development'
            },
            'analysis': None
        }
        
        return self.create(project_data)
    
    def find_by_project_id(self, project_id):
        """Find project by project_id"""
        return self.find_by_id(project_id, 'project_id')
    
    def find_by_user(self, user_id, limit=50, skip=0):
        """Find projects by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def update_project(self, project_id, data):
        """Update project"""
        allowed_fields = ['name', 'description', 'status', 'settings', 'metadata']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        return self.update(project_id, update_data, 'project_id')
    
    def update_analysis(self, project_id, analysis):
        """Update project analysis"""
        return self.update(project_id, {'analysis': analysis}, 'project_id')
    
    def delete_project(self, project_id):
        """Delete project"""
        return self.delete(project_id, 'project_id')
    
    def get_project_stats(self, user_id=None):
        """Get project statistics"""
        query = {'user_id': user_id} if user_id else {}
        
        total = self.count(query)
        by_status = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ])
        
        return {
            'total_projects': total,
            'by_status': {item['_id']: item['count'] for item in by_status}
        }