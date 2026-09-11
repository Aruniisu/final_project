#!/usr/bin/env python
"""
🔍 SYSTEM DIAGNOSTIC TEST - මොනවද වැඩ කරන්නේ කියලා බලමු
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("🔍 SMART DEVOPS SYSTEM DIAGNOSTIC")
print("="*60)
print()

# ============================================
# TEST 1: Check Database Connection
# ============================================
print("📊 TEST 1: Database Connection")
print("-"*40)

try:
    from database.connection import db_connection
    print("✅ database.connection module found")
    
    # Try to connect
    from flask import Flask
    test_app = Flask(__name__)
    test_app.config['MONGO_URI'] = 'mongodb://localhost:27017/'
    test_app.config['MONGODB_DB'] = 'smart_devops'
    
    if db_connection.init_app(test_app):
        print("✅ MongoDB connected successfully!")
        db = db_connection.get_db()
        print(f"   Database: {db_connection.database_name}")
        print(f"   Collections: {db.list_collection_names() if db else 'None'}")
    else:
        print("❌ MongoDB connection failed!")
        print("   ⚠️ Please start MongoDB: mongod")
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ============================================
# TEST 2: Check Agents
# ============================================
print("🤖 TEST 2: AI Agents")
print("-"*40)

try:
    from agents.orchestrator import Orchestrator
    print("✅ Orchestrator imported successfully")
    
    from agents.executor_agent import ExecutorAgent
    print("✅ ExecutorAgent imported successfully")
    
    from agents.self_healing_agent import SelfHealingAgent
    print("✅ SelfHealingAgent imported successfully")
    
    from agents.base_agent import BaseAgent
    print("✅ BaseAgent imported successfully")
    
    # Test Orchestrator
    print("\n🧪 Testing Orchestrator...")
    orch = Orchestrator()
    result = orch.process(
        {'action': 'chat', 'query': 'Deploy my project'},
        context={'project_name': 'Test'}
    )
    
    print(f"   Response: {result.get('response', '')[:50]}...")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Steps: {len(result.get('steps', []))}")
    
    if result.get('response'):
        print("✅ Orchestrator is working!")
    else:
        print("❌ Orchestrator returned empty response")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ============================================
# TEST 3: Check API Routes
# ============================================
print("🌐 TEST 3: API Routes")
print("-"*40)

try:
    from api.assistant import assistant_bp
    print("✅ assistant API loaded")
    
    # Check if routes exist
    routes = []
    for rule in assistant_bp.url_map.iter_rules() if hasattr(assistant_bp, 'url_map') else []:
        routes.append(rule.rule)
    
    print(f"   Routes: {routes if routes else 'Check manually'}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ============================================
# TEST 4: Check WebSocket
# ============================================
print("🔌 TEST 4: WebSocket")
print("-"*40)

try:
    import eventlet
    print("✅ eventlet available")
except ImportError:
    print("⚠️ eventlet not installed (WebSocket may not work)")

try:
    from flask_socketio import SocketIO
    print("✅ flask-socketio available")
except ImportError:
    print("❌ flask-socketio not installed")

print()

# ============================================
# TEST 5: Check Docker & Kubernetes
# ============================================
print("🐳 TEST 5: Docker & Kubernetes")
print("-"*40)

try:
    import docker
    client = docker.from_env()
    client.ping()
    print("✅ Docker is running!")
except ImportError:
    print("❌ docker module not installed")
except Exception as e:
    print(f"❌ Docker error: {e}")

try:
    from kubernetes import client, config
    config.load_kube_config()
    print("✅ Kubernetes config loaded")
except ImportError:
    print("❌ kubernetes module not installed")
except Exception as e:
    print(f"⚠️ Kubernetes: {e}")

print()

# ============================================
# SUMMARY
# ============================================
print("="*60)
print("📋 SUMMARY")
print("="*60)

issues = []

print("\n🔴 ISSUES FOUND:")
print("-"*40)

# Check database
if 'db_connection' not in dir() or not db_connection.is_connected():
    issues.append("❌ MongoDB not connected - Start MongoDB")
    print("   ❌ MongoDB not connected")
else:
    print("   ✅ MongoDB connected")

# Check agents
try:
    orch = Orchestrator()
    test_result = orch.process({'action': 'test'})
    if test_result:
        print("   ✅ Agents working")
    else:
        issues.append("❌ Agents not responding")
        print("   ❌ Agents not responding")
except:
    issues.append("❌ Agents not imported properly")
    print("   ❌ Agents not imported properly")

# Check Docker
try:
    import docker
    client = docker.from_env()
    client.ping()
    print("   ✅ Docker running")
except:
    issues.append("❌ Docker not running")
    print("   ❌ Docker not running")

print("\n" + "="*60)

if issues:
    print(f"\n⚠️ Found {len(issues)} issue(s):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n🔧 Please fix these issues first.")
else:
    print("\n✅ ALL SYSTEMS WORKING!")

print("\n💡 Next steps:")
print("   1. Run: python src/app.py")
print("   2. Open: http://localhost:3000")
print("   3. Type: 'Deploy my project'")