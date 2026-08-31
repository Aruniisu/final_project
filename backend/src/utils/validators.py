import re
from datetime import datetime

def validate_email(email):
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

def validate_phone(phone):
    """Validate phone number"""
    pattern = r'^\+?[\d\s-]{10,15}$'
    return bool(re.match(pattern, phone))

def validate_url(url):
    """Validate URL"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def validate_ip(ip):
    """Validate IP address"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def validate_port(port):
    """Validate port number"""
    try:
        port = int(port)
        return 1 <= port <= 65535
    except:
        return False

def validate_date(date_str, format='%Y-%m-%d'):
    """Validate date string"""
    try:
        datetime.strptime(date_str, format)
        return True
    except:
        return False

def validate_datetime(dt_str):
    """Validate datetime string"""
    try:
        datetime.fromisoformat(dt_str)
        return True
    except:
        return False

def validate_json_schema(data, schema):
    """Validate data against JSON schema"""
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Check field types
    for field, rules in properties.items():
        if field in data:
            if 'type' in rules:
                expected_type = rules['type']
                if expected_type == 'string' and not isinstance(data[field], str):
                    return False, f"Field {field} must be a string"
                elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                    return False, f"Field {field} must be a number"
                elif expected_type == 'integer' and not isinstance(data[field], int):
                    return False, f"Field {field} must be an integer"
                elif expected_type == 'boolean' and not isinstance(data[field], bool):
                    return False, f"Field {field} must be a boolean"
                elif expected_type == 'array' and not isinstance(data[field], list):
                    return False, f"Field {field} must be an array"
                elif expected_type == 'object' and not isinstance(data[field], dict):
                    return False, f"Field {field} must be an object"
            
            if 'min_length' in rules and len(data[field]) < rules['min_length']:
                return False, f"Field {field} must be at least {rules['min_length']} characters"
            
            if 'max_length' in rules and len(data[field]) > rules['max_length']:
                return False, f"Field {field} must be at most {rules['max_length']} characters"
            
            if 'pattern' in rules and not re.match(rules['pattern'], str(data[field])):
                return False, f"Field {field} has invalid format"
    
    return True, "Valid"

def sanitize_string(text):
    """Sanitize string"""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>{}]', '', text)
    # Escape HTML
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)

def sanitize_object(obj):
    """Sanitize object recursively"""
    if isinstance(obj, str):
        return sanitize_string(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_object(item) for item in obj]
    else:
        return obj