import uuid
import hashlib
import re
from datetime import datetime, timedelta
from functools import wraps
import json

def generate_id(prefix=''):
    """Generate unique ID"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}" if prefix else uuid.uuid4().hex[:12]

def generate_slug(text):
    """Generate URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text

def hash_string(text):
    """Hash a string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()

def format_timestamp(dt):
    """Format datetime to ISO string"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt

def parse_timestamp(ts):
    """Parse timestamp string to datetime"""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        return datetime.fromisoformat(ts)
    return None

def truncate_text(text, max_length=100):
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

def extract_keywords(text, limit=10):
    """Extract keywords from text"""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    from collections import Counter
    return [word for word, count in Counter(words).most_common(limit)]

def safe_json_loads(text):
    """Safely load JSON"""
    try:
        return json.loads(text)
    except:
        return None

def safe_json_dumps(data):
    """Safely dump JSON"""
    try:
        return json.dumps(data)
    except:
        return str(data)

def paginate_list(items, page=1, per_page=20):
    """Paginate a list"""
    start = (page - 1) * per_page
    end = start + per_page
    return {
        'items': items[start:end],
        'total': len(items),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(items) + per_page - 1) // per_page
    }

def validate_url(url):
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def get_file_extension(filename):
    """Get file extension"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def is_allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    ext = get_file_extension(filename)
    return ext in allowed_extensions

def human_readable_size(size):
    """Convert size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry function on failure"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            import time
            last_error = None
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_error
        return decorated
    return decorator

def timing_decorator(f):
    """Decorator to time function execution"""
    @wraps(f)
    def decorated(*args, **kwargs):
        import time
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f"{f.__name__} took {end - start:.2f} seconds")
        return result
    return decorated