"""
Central Event Bus — Cross-Page Real-Time Sync
==============================================
Broadcasts state changes to all connected clients via Socket.IO.
"""

import time
from datetime import datetime
from collections import deque

_socketio = None
EVENT_HISTORY = deque(maxlen=200)


def set_socketio(socketio_instance):
    global _socketio
    _socketio = socketio_instance
    print("✅ Event Bus → Socket.IO connected")


def emit_event(event_type: str, data: dict = None, room: str = None):
    payload = {
        'type': event_type,
        'data': data or {},
        'timestamp': time.time(),
        'iso': datetime.now().isoformat(),
    }
    EVENT_HISTORY.append(payload)
    if _socketio:
        try:
            if room:
                _socketio.emit('platform_event', payload, room=room)
            else:
                _socketio.emit('platform_event', payload)
        except Exception as e:
            print(f"⚠️  Event Bus emit failed: {e}")
    print(f"📡 [Event] {event_type}")


def get_recent_events(limit: int = 50) -> list:
    return list(EVENT_HISTORY)[-limit:]


def clear_history():
    EVENT_HISTORY.clear()