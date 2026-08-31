from datetime import datetime
from bson import ObjectId
import uuid

class Upload:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.uploads

    def create(self, user_id, project_id, files=None, source='file', metadata=None):
        """Create an upload record"""
        upload_data = {
            'upload_id': str(uuid.uuid4()),
            'user_id': user_id,
            'project_id': project_id,
            'source': source,
            'files': files or [],
            'status': 'completed',
            'metadata': metadata or {},
            'created_at': datetime.now()
        }
        
        result = self.collection.insert_one(upload_data)
        upload_data['_id'] = str(result.inserted_id)
        return upload_data

    def find_by_id(self, upload_id):
        """Find upload by ID"""
        try:
            upload = self.collection.find_one({'upload_id': upload_id})
            if upload:
                upload['_id'] = str(upload['_id'])
            return upload
        except:
            return None

    def find_by_user(self, user_id, limit=50, offset=0):
        """Find uploads by user"""
        uploads = list(self.collection.find(
            {'user_id': user_id}
        ).skip(offset).limit(limit).sort('created_at', -1))
        
        for upload in uploads:
            upload['_id'] = str(upload['_id'])
        return uploads

    def find_by_project(self, project_id):
        """Find uploads by project"""
        uploads = list(self.collection.find(
            {'project_id': project_id}
        ).sort('created_at', -1))
        
        for upload in uploads:
            upload['_id'] = str(upload['_id'])
        return uploads

    def delete(self, upload_id):
        """Delete upload"""
        result = self.collection.delete_one({'upload_id': upload_id})
        return result.deleted_count > 0