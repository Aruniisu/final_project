import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Health: {response.json()}")
    return response.json()

def test_register():
    """Test user registration"""
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
    print(f"Register: {response.json()}")
    return response.json()

def test_login():
    """Test user login"""
    data = {
        "email": "test@example.com",
        "password": "Test@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
    print(f"Login: {response.json()}")
    return response.json()

def test_upload():
    """Test file upload"""
    # First login to get token
    login_data = {
        "email": "test@example.com",
        "password": "Test@123"
    }
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    token = login_response.json().get('token')
    
    if not token:
        print("❌ Login failed, cannot upload")
        return
    
    # Upload a test file
    files = {'files': ('test.txt', 'This is a test file content')}
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/upload/files", files=files, headers=headers)
    print(f"Upload: {response.json()}")
    return response.json()

def test_pipeline():
    """Test pipeline creation"""
    # First login to get token
    login_data = {
        "email": "test@example.com",
        "password": "Test@123"
    }
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    token = login_response.json().get('token')
    
    if not token:
        print("❌ Login failed")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create pipeline
    data = {
        "name": "Test Pipeline",
        "repo": "test/repo",
        "branch": "main"
    }
    response = requests.post(f"{BASE_URL}/api/pipelines", json=data, headers=headers)
    print(f"Pipeline: {response.json()}")
    return response.json()

def test_monitoring():
    """Test monitoring endpoint"""
    response = requests.get(f"{BASE_URL}/api/monitoring/metrics")
    print(f"Monitoring: {response.json()}")
    return response.json()

if __name__ == "__main__":
    print("="*50)
    print("Testing Smart DevOps API")
    print("="*50)
    
    print("\n1. Health Check:")
    test_health()
    
    print("\n2. Register User:")
    test_register()
    
    print("\n3. Login User:")
    test_login()
    
    print("\n4. Upload File:")
    test_upload()
    
    print("\n5. Create Pipeline:")
    test_pipeline()
    
    print("\n6. Monitoring Metrics:")
    test_monitoring()
    
    print("\n" + "="*50)
    print("✅ Testing Complete!")