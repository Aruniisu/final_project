import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

# Ensure root and src directories can be imported properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# ------------------------------------------------------------
# 1. Flask App Initialization
# ------------------------------------------------------------
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['MONGO_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
app.config['MONGODB_DB'] = os.getenv('MONGODB_DB', 'smart_devops')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ------------------------------------------------------------
# 2. CORS & WebSocket Configuration
# ------------------------------------------------------------
CORS(app, resources={r"/api/*": {"origins": "*"}})

try:
    import eventlet
    async_mode = 'eventlet'
except ImportError:
    async_mode = 'threading'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=async_mode,
    logger=True,
    engineio_logger=True
)

# Helper function to broadcast live execution logs directly to frontend terminal
def stream_terminal_log(message, log_type="info", sid=None):
    payload = {
        'log': message,
        'type': log_type,  # 'info', 'success', 'warning', 'error'
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    if sid:
        socketio.emit('live_log', payload, room=sid)
    else:
        socketio.emit('live_log', payload)

# ------------------------------------------------------------
# 3. Database Connection
# ------------------------------------------------------------
db = None
db_connection = None

try:
    from database.connection import db_connection
    if db_connection.init_app(app):
        print("✅ Database connected successfully!")
        db = db_connection.get_db()
    else:
        print("❌ Database connection failed!")
except ImportError:
    print("⚠️  database.connection not found – using dummy connection.")
    class DummyDB:
        def init_app(self, app): return False
        def get_db(self): return None
        def is_connected(self): return False
        def get_stats(self): return {'status': 'disconnected', 'collections_list': []}
    db_connection = DummyDB()
    db = None

# ------------------------------------------------------------
# 4. Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# 5. Dynamic Blueprint Registration
# ------------------------------------------------------------
blueprint_defs = [
    ('api.auth', 'auth_bp', '/api/auth'),
    ('api.assistant', 'assistant_bp', '/api/assistant'),
    ('api.upload', 'upload_bp', '/api/upload'),
    ('api.pipelines', 'pipelines_bp', '/api/pipelines'),
    ('api.infrastructure', 'infrastructure_bp', '/api/infrastructure'),
    ('api.monitoring', 'monitoring_bp', '/api/monitoring'),
    ('api.training', 'training_bp', '/api/training'),
    ('api.settings', 'settings_bp', '/api/settings'),
]

blueprints_loaded = []
for module_name, bp_name, url_prefix in blueprint_defs:
    try:
        module = __import__(module_name, fromlist=[bp_name])
        bp = getattr(module, bp_name)
        app.register_blueprint(bp, url_prefix=url_prefix)
        blueprints_loaded.append(url_prefix)
        logger.info(f"✅ Registered {url_prefix}")
    except (ImportError, AttributeError) as e:
        logger.warning(f"⚠️  Could not load {module_name}: {e}")

# ------------------------------------------------------------
# 6. WebSocket Real-time Events (Live Terminal & Agent Communication)
# ------------------------------------------------------------
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    join_room(request.sid)
    emit('connected', {
        'message': 'Connected to Smart DevOps Engine',
        'sid': request.sid,
        'timestamp': datetime.now().isoformat()
    })
    # Initial system message on UI terminal
    stream_terminal_log("Agent Socket Stream Online. Ready for commands...", "success", sid=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    leave_room(request.sid)

@socketio.on('chat')
def handle_chat(data):
    """Handles Chat Prompts from Frontend"""
    sid = request.sid
    try:
        message = data.get('message', '')
        user_id = data.get('user_id', 'anonymous')
        
        stream_terminal_log(f"Received instruction: '{message}'", "info", sid=sid)
        
        # Import Orchestrator from src.agents
        from src.agents import Orchestrator
        orchestrator = Orchestrator()
        
        # Process the chat input
        response = orchestrator.process(
            {'action': 'chat', 'query': message}, 
            context={'user_id': user_id, 'sid': sid}
        )
        
        reply_text = response.get('response', response) if isinstance(response, dict) else str(response)
        
        emit('chat_response', {
            'message': reply_text,
            'timestamp': datetime.now().isoformat()
        }, room=sid)
        
    except ImportError as e:
        stream_terminal_log(f"Error: Agent Orchestrator module not loaded. Details: {e}", "error", sid=sid)
        emit('chat_response', {'error': 'Orchestrator not available'}, room=sid)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        stream_terminal_log(f"Execution Error: {str(e)}", "error", sid=sid)
        emit('chat_response', {'error': str(e)}, room=sid)

@socketio.on('devops_action')
def handle_quick_action(data):
    """Handles Action Buttons on UI (Deploy, Pipeline, Fix Code, Security, Scale)"""
    sid = request.sid
    action_type = data.get('action')  # e.g. 'deploy', 'pipeline', 'fix_code', 'scale'
    project_id = data.get('project_id', 'default_project')
    
    stream_terminal_log(f"Executing quick action: [{str(action_type).upper()}] on {project_id}", "info", sid=sid)
    
    try:
        from src.agents import Orchestrator
        orchestrator = Orchestrator()
        
        result = orchestrator.process(
            {'action': action_type, 'project_id': project_id, 'data': data}, 
            context={'sid': sid}
        )
        emit('action_response', {'status': 'success', 'result': result}, room=sid)
    except Exception as e:
        logger.error(f"Action error: {e}")
        stream_terminal_log(f"Action failed: {str(e)}", "error", sid=sid)
        emit('action_response', {'status': 'failed', 'error': str(e)}, room=sid)

# ------------------------------------------------------------
# 7. System Health Check
# ------------------------------------------------------------
@app.route('/api/health')
def health_check():
    db_stats = db_connection.get_stats() if db_connection else {'status': 'disconnected'}
    return jsonify({
        'status': 'healthy' if db_stats.get('status') == 'connected' else 'degraded',
        'database': db_stats.get('status', 'unknown'),
        'registered_blueprints': blueprints_loaded,
        'timestamp': datetime.now().isoformat(),
        'version': '2.3.1'
    })

# ------------------------------------------------------------
# 8. Run Application
# ------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Smart DevOps Backend running on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)