from .base_manager import BaseManager
from datetime import datetime


class UploadManager(BaseManager):
    """Manager for upload operations"""
    
    def __init__(self, db):
        super().__init__(db, 'uploads')
    
    def create_upload(self, user_id, project_id, files=None, source='file', metadata=None):
        """Create an upload record"""
        upload_data = {
            'upload_id': self._generate_id('up'),
            'user_id': user_id,
            'project_id': project_id,
            'source': source,
            'files': files or [],
            'status': 'completed',
            'metadata': metadata or {},
            'created_at': datetime.now()
        }
        
        return self.create(upload_data)
    
    def find_by_upload_id(self, upload_id):
        """Find upload by upload_id"""
        return self.find_by_id(upload_id, 'upload_id')
    
    def find_by_user(self, user_id, limit=50, skip=0):
        """Find uploads by user"""
        return self.find_many(
            {'user_id': user_id},
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )
    
    def find_by_project(self, project_id):
        """Find uploads by project"""
        return self.find_many(
            {'project_id': project_id},
            sort=[('created_at', -1)]
        )
    
    def update_upload(self, upload_id, data):
        """Update upload"""
        allowed_fields = ['status', 'metadata', 'files']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        return self.update(upload_id, update_data, 'upload_id')
    
    def delete_upload(self, upload_id):
        """Delete upload"""
        return self.delete(upload_id, 'upload_id')
    
    def get_upload_stats(self, user_id=None):
        """Get upload statistics"""
        query = {'user_id': user_id} if user_id else {}
        
        total = self.count(query)
        by_source = self.aggregate([
            {'$match': query},
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
        ])
        
        return {
            'total_uploads': total,
            'by_source': {item['_id']: item['count'] for item in by_source}
        }