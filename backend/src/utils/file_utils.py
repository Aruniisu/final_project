import os
import shutil
import zipfile
import tarfile
import tempfile
from pathlib import Path
import mimetypes

def ensure_directory(path):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)
    return path

def get_file_size(path):
    """Get file size in bytes"""
    return os.path.getsize(path)

def get_file_mime_type(path):
    """Get file MIME type"""
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or 'application/octet-stream'

def is_text_file(path):
    """Check if file is text"""
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.jsx', '.ts', '.tsx',
        '.json', '.yaml', '.yml', '.toml', '.xml', '.html',
        '.css', '.scss', '.csv', '.log', '.ini', '.cfg',
        '.conf', '.sh', '.bash', '.zsh', '.env'
    }
    ext = os.path.splitext(path)[1].lower()
    return ext in text_extensions

def read_file_content(path, encoding='utf-8'):
    """Read file content"""
    try:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            return f.read()

def write_file_content(path, content, encoding='utf-8'):
    """Write file content"""
    ensure_directory(os.path.dirname(path))
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)

def delete_file(path):
    """Delete file"""
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def delete_directory(path):
    """Delete directory"""
    if os.path.exists(path):
        shutil.rmtree(path)
        return True
    return False

def copy_file(src, dst):
    """Copy file"""
    ensure_directory(os.path.dirname(dst))
    shutil.copy2(src, dst)
    return dst

def move_file(src, dst):
    """Move file"""
    ensure_directory(os.path.dirname(dst))
    shutil.move(src, dst)
    return dst

def create_zip_file(source_dir, output_path):
    """Create zip archive from directory"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    return output_path

def extract_zip_file(zip_path, extract_to):
    """Extract zip archive"""
    ensure_directory(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_to)
    return extract_to

def create_tar_file(source_dir, output_path, compression='gz'):
    """Create tar archive"""
    mode = 'w:gz' if compression == 'gz' else 'w'
    with tarfile.open(output_path, mode) as tarf:
        tarf.add(source_dir, arcname=os.path.basename(source_dir))
    return output_path

def extract_tar_file(tar_path, extract_to):
    """Extract tar archive"""
    ensure_directory(extract_to)
    with tarfile.open(tar_path, 'r:*') as tarf:
        tarf.extractall(extract_to)
    return extract_to

def get_file_list(directory, recursive=True, extensions=None):
    """Get list of files in directory"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if extensions:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue
            files.append(file_path)
        if not recursive:
            break
    return files

def get_directory_size(directory):
    """Get directory size in bytes"""
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total

def safe_filename(filename):
    """Create safe filename"""
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    # Remove dangerous characters
    import re
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

def get_temp_dir(prefix='tmp'):
    """Get temporary directory"""
    return tempfile.mkdtemp(prefix=prefix)

def cleanup_temp_dir(temp_dir):
    """Clean up temporary directory"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)