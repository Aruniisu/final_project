import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)

# Global reference for SocketIO emitting (Injected from main app)
socketio_instance = None

def set_socketio(sio):
    """Register global socketio instance for streaming logs to frontend"""
    global socketio_instance
    socketio_instance = sio

class BaseAgent(ABC):
    """Base class for all AI agents with full real-time event emitting functionality"""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.agent_id = str(uuid.uuid4())[:8]
        self.name = name
        self.config = config or {}
        self.state = {}
        self.memory = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metrics = {
            'tasks_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'avg_response_time': 0
        }
        self.history = []
        self.tools = []
        self._register_tools()
    
    @abstractmethod
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """Process input and return output"""
        pass
    
    def _register_tools(self):
        """Register available tools for this agent"""
        pass

    def emit_log(self, message: str, level: str = 'info', sid: Optional[str] = None):
        """Emit real-time logs to UI terminal via WebSockets and record activity"""
        self.log_activity(message, level)
        
        if socketio_instance:
            log_payload = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'agent': self.name,
                'message': message,
                'level': level
            }
            try:
                if sid:
                    socketio_instance.emit('agent_log', log_payload, room=sid)
                else:
                    socketio_instance.emit('agent_log', log_payload)
            except Exception as e:
                logger.error(f"Failed to emit socket log: {e}")

    def update_state(self, key: str, value: Any):
        """Update agent state"""
        self.state[key] = value
        self.last_activity = datetime.now()
    
    def get_state(self, key: Optional[str] = None):
        """Get agent state"""
        if key:
            return self.state.get(key)
        return self.state
    
    def add_memory(self, memory: Dict):
        """Add memory entry"""
        memory['timestamp'] = datetime.now().isoformat()
        self.memory.append(memory)
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
    
    def log_activity(self, message: str, level: str = 'info', data: Optional[Dict] = None):
        """Log agent activity with structured data"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'agent_id': self.agent_id,
            'level': level,
            'message': message,
            'data': data or {}
        }
        self.history.append(log_entry)
        self.last_activity = datetime.now()
        
        if level == 'info':
            logger.info(f"[{self.name}] {message}")
        elif level == 'warning' or level == 'warn':
            logger.warning(f"[{self.name}] {message}")
        elif level == 'error' or level == 'critical':
            logger.error(f"[{self.name}] {message}")
    
    def track_metric(self, success: bool, response_time: float):
        """Track performance metrics"""
        self.metrics['tasks_processed'] += 1
        if success:
            self.metrics['success_count'] += 1
        else:
            self.metrics['error_count'] += 1
        
        total = self.metrics['tasks_processed']
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total
    
    def get_metrics(self) -> Dict:
        """Get agent metrics"""
        return {
            **self.metrics,
            'success_rate': (self.metrics['success_count'] / self.metrics['tasks_processed'] * 100) if self.metrics['tasks_processed'] > 0 else 0
        }
    
    def to_dict(self) -> Dict:
        """Convert agent to dictionary"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'state': self.state,
            'metrics': self.get_metrics(),
            'history': self.history[-20:],
            'memory': self.memory[-10:],
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }