"""ProjectManager — Basic project management for single-user"""
from datetime import datetime
from bson import ObjectId


class ProjectManager:
    def __init__(self, db):
        self.db = db
        self.collection = db.projects

    def create_project(self, user_id, name, repo_url=None, source='github'):
        project = {
            'project_id': str(ObjectId()),
            'user_id': user_id,
            'name': name,
            'repo_url': repo_url,
            'source': source,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        result = self.collection.insert_one(project)
        project['_id'] = str(result.inserted_id)
        return project

    def get_projects(self, user_id):
        projects = list(self.collection.find({'user_id': user_id}))
        for p in projects:
            p['_id'] = str(p['_id'])
        return projects

    def get_project(self, project_id):
        p = self.collection.find_one({'project_id': project_id})
        if p:
            p['_id'] = str(p['_id'])
        return p

    def delete_project(self, project_id):
        result = self.collection.delete_one({'project_id': project_id})
        return result.deleted_count > 0

    def count(self):
        return self.collection.count_documents({})