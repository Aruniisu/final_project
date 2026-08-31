from datetime import datetime
from bson import ObjectId
import uuid
import logging

logger = logging.getLogger(__name__)


class BaseManager:
    """Base manager class with common database operations"""
    
    def __init__(self, db, collection_name):
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name
    
    def _generate_id(self, prefix=''):
        """Generate unique ID"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}" if prefix else uuid.uuid4().hex[:12]
    
    def _format_document(self, doc):
        """Format MongoDB document"""
        if not doc:
            return None
        doc['_id'] = str(doc['_id'])
        return doc
    
    def _format_documents(self, docs):
        """Format multiple documents"""
        return [self._format_document(doc) for doc in docs] if docs else []
    
    def create(self, data):
        """Create a new document"""
        try:
            data['created_at'] = datetime.now()
            data['updated_at'] = datetime.now()
            result = self.collection.insert_one(data)
            data['_id'] = str(result.inserted_id)
            return data
        except Exception as e:
            logger.error(f"Error creating {self.collection_name}: {e}")
            return None
    
    def find_by_id(self, doc_id, id_field='_id'):
        """Find document by ID"""
        try:
            if id_field == '_id':
                query = {'_id': ObjectId(doc_id)}
            else:
                query = {id_field: doc_id}
            doc = self.collection.find_one(query)
            return self._format_document(doc)
        except Exception as e:
            logger.error(f"Error finding {self.collection_name} by ID: {e}")
            return None
    
    def find_one(self, query):
        """Find one document matching query"""
        try:
            doc = self.collection.find_one(query)
            return self._format_document(doc)
        except Exception as e:
            logger.error(f"Error finding one {self.collection_name}: {e}")
            return None
    
    def find_many(self, query=None, sort=None, limit=50, skip=0):
        """Find multiple documents matching query"""
        try:
            cursor = self.collection.find(query or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if skip:
                cursor = cursor.skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return self._format_documents(list(cursor))
        except Exception as e:
            logger.error(f"Error finding {self.collection_name}: {e}")
            return []
    
    def update(self, doc_id, data, id_field='_id'):
        """Update a document"""
        try:
            if id_field == '_id':
                query = {'_id': ObjectId(doc_id)}
            else:
                query = {id_field: doc_id}
            
            data['updated_at'] = datetime.now()
            result = self.collection.update_one(query, {'$set': data})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating {self.collection_name}: {e}")
            return False
    
    def delete(self, doc_id, id_field='_id'):
        """Delete a document"""
        try:
            if id_field == '_id':
                query = {'_id': ObjectId(doc_id)}
            else:
                query = {id_field: doc_id}
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting {self.collection_name}: {e}")
            return False
    
    def count(self, query=None):
        """Count documents"""
        try:
            return self.collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"Error counting {self.collection_name}: {e}")
            return 0
    
    def aggregate(self, pipeline):
        """Run aggregation pipeline"""
        try:
            result = self.collection.aggregate(pipeline)
            return list(result)
        except Exception as e:
            logger.error(f"Error aggregating {self.collection_name}: {e}")
            return []
    
    def exists(self, query):
        """Check if document exists"""
        try:
            return self.collection.find_one(query) is not None
        except Exception as e:
            logger.error(f"Error checking existence in {self.collection_name}: {e}")
            return False
    
    def bulk_insert(self, documents):
        """Insert multiple documents"""
        try:
            for doc in documents:
                doc['created_at'] = datetime.now()
                doc['updated_at'] = datetime.now()
            result = self.collection.insert_many(documents)
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Error bulk inserting in {self.collection_name}: {e}")
            return []
    
    def bulk_update(self, updates):
        """Update multiple documents"""
        try:
            for update in updates:
                update['$set']['updated_at'] = datetime.now()
            result = self.collection.bulk_write(updates)
            return result.modified_count
        except Exception as e:
            logger.error(f"Error bulk updating in {self.collection_name}: {e}")
            return 0