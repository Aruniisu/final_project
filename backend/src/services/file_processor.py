import os
import shutil
import zipfile
import tarfile
import tempfile
import json
import yaml
import re
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service for processing uploaded files"""
    
    ALLOWED_EXTENSIONS = {
        'zip', 'tar', 'gz', 'tgz', 'rar', '7z',
        'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'go', 'rs',
        'json', 'yaml', 'yml', 'toml', 'xml',
        'txt', 'md', 'rst', 'html', 'css', 'scss',
        'png', 'jpg', 'jpeg', 'svg', 'gif', 'ico',
        'pdf', 'doc', 'docx', 'xls', 'xlsx'
    }
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, upload_dir=None):
        self.upload_dir = upload_dir or os.getenv('UPLOAD_FOLDER', './uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def process_file(self, file, filename=None):
        """Process uploaded file"""
        filename = filename or file.filename
        
        # Validate
        if not self.is_allowed_file(filename):
            raise ValueError(f"File type not allowed: {filename}")
        
        if file.content_length and file.content_length > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file.content_length} bytes")
        
        # Generate safe filename
        safe_filename = self.generate_safe_filename(filename)
        filepath = os.path.join(self.upload_dir, safe_filename)
        
        # Save file
        file.save(filepath)
        
        # Get file info
        file_info = {
            'filename': filename,
            'safe_filename': safe_filename,
            'path': filepath,
            'size': os.path.getsize(filepath),
            'extension': self.get_extension(filename),
            'mime_type': file.mimetype,
            'hash': self.calculate_hash(filepath),
            'processed_at': datetime.now().isoformat()
        }
        
        # Process based on type
        if self.is_archive(filename):
            extracted_path = self.extract_archive(filepath)
            file_info['extracted_path'] = extracted_path
            file_info['extracted_files'] = self.list_files(extracted_path)
        
        return file_info
    
    def is_allowed_file(self, filename):
        """Check if file type is allowed"""
        ext = self.get_extension(filename)
        return ext in self.ALLOWED_EXTENSIONS
    
    def is_archive(self, filename):
        """Check if file is an archive"""
        ext = self.get_extension(filename)
        return ext in ['zip', 'tar', 'gz', 'tgz', 'rar', '7z']
    
    def is_image(self, filename):
        """Check if file is an image"""
        ext = self.get_extension(filename)
        return ext in ['png', 'jpg', 'jpeg', 'svg', 'gif', 'ico']
    
    def is_code_file(self, filename):
        """Check if file is a code file"""
        ext = self.get_extension(filename)
        return ext in ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'go', 'rs', 'c', 'cpp', 'h', 'hpp']
    
    def get_extension(self, filename):
        """Get file extension"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    def generate_safe_filename(self, filename):
        """Generate safe filename"""
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        # Remove dangerous characters
        return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    def calculate_hash(self, filepath, algorithm='md5'):
        """Calculate file hash"""
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def extract_archive(self, filepath, target_dir=None):
        """Extract archive file"""
        if not target_dir:
            target_dir = os.path.join(self.upload_dir, 'extracted_' + os.path.basename(filepath))
        
        os.makedirs(target_dir, exist_ok=True)
        
        ext = self.get_extension(filepath)
        
        if ext == 'zip':
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall(target_dir)
        elif ext in ['tar', 'gz', 'tgz']:
            mode = 'r:gz' if ext in ['gz', 'tgz'] else 'r'
            with tarfile.open(filepath, mode) as tarf:
                tarf.extractall(target_dir)
        else:
            raise ValueError(f"Unsupported archive format: {ext}")
        
        return target_dir
    
    def list_files(self, directory, recursive=True):
        """List files in directory"""
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                files.append({
                    'path': filepath,
                    'name': filename,
                    'relative_path': os.path.relpath(filepath, directory),
                    'size': os.path.getsize(filepath),
                    'extension': self.get_extension(filename)
                })
            if not recursive:
                break
        return files
    
    def read_file_content(self, filepath, encoding='utf-8'):
        """Read file content"""
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            with open(filepath, 'rb') as f:
                return f.read()
    
    def parse_config_file(self, filepath):
        """Parse configuration file"""
        ext = self.get_extension(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if ext == 'json':
                return json.loads(content)
            elif ext in ['yaml', 'yml']:
                return yaml.safe_load(content)
            else:
                return {'content': content, 'format': ext}
        except Exception as e:
            logger.error(f"Error parsing config file {filepath}: {e}")
            return None
    
    def delete_file(self, filepath):
        """Delete file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
        return False
    
    def delete_directory(self, directory):
        """Delete directory"""
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                return True
        except Exception as e:
            logger.error(f"Error deleting directory {directory}: {e}")
        return False
    
    def move_file(self, src, dst):
        """Move file"""
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return dst
        except Exception as e:
            logger.error(f"Error moving file {src} to {dst}: {e}")
            return None