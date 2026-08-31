import os
import io
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class DriveService:
    """Service for interacting with Google Drive API"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path=None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = 'token.pickle'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def list_files(self, query=None, page_size=100):
        """List files in Google Drive"""
        try:
            results = self.service.files().list(
                q=query or "mimeType != 'application/vnd.google-apps.folder'",
                pageSize=page_size,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            return [{
                'id': f['id'],
                'name': f['name'],
                'mime_type': f.get('mimeType'),
                'size': f.get('size'),
                'created_at': f.get('createdTime'),
                'modified_at': f.get('modifiedTime'),
                'url': f.get('webViewLink')
            } for f in files]
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise
    
    def get_file(self, file_id):
        """Get file metadata"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents"
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'mime_type': file.get('mimeType'),
                'size': file.get('size'),
                'created_at': file.get('createdTime'),
                'modified_at': file.get('modifiedTime'),
                'url': file.get('webViewLink'),
                'parents': file.get('parents', [])
            }
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise
    
    def download_file(self, file_id, target_path=None):
        """Download file from Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            if target_path:
                # Download to file
                with open(target_path, 'wb') as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            logger.info(f"Download progress: {int(status.progress() * 100)}%")
                return target_path
            else:
                # Download to memory
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                fh.seek(0)
                return fh.read()
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise
    
    def upload_file(self, file_path, name=None, folder_id=None):
        """Upload file to Google Drive"""
        try:
            name = name or os.path.basename(file_path)
            media = MediaFileUpload(file_path, resumable=True)
            
            file_metadata = {'name': name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'url': file.get('webViewLink')
            }
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise
    
    def create_folder(self, name, parent_id=None):
        """Create folder in Google Drive"""
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()
            
            return {
                'id': folder['id'],
                'name': folder['name']
            }
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise
    
    def delete_file(self, file_id):
        """Delete file from Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            return False
    
    def search_files(self, query, max_results=50):
        """Search files in Google Drive"""
        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            logger.error(f"Drive API error: {e}")
            raise