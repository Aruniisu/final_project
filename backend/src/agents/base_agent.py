"""
Base Agent — High-Performance Agentic AI Foundation
+ Cross-page event emission + ML feedback + Notifications
"""

import os, json, logging, uuid, time, zlib, traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


def stable_hash(s: str) -> int:
    return zlib.crc32((s or '').encode('utf-8')) % 100


try:
    from core.event_bus import emit_event
    print("✅ [base_agent] Event bus loaded OK")
except Exception as _e:
    def emit_event(*args, **kwargs): pass
    print(f"❌ [base_agent] Event bus FAILED: {_e}")

try:
    from ml.feedback import log_action as _ml_log
    print("✅ [base_agent] ML feedback loaded OK")
except Exception as _e:
    def _ml_log(*args, **kwargs): pass
    print(f"❌ [base_agent] ML feedback FAILED: {_e}")


socketio_instance = None

def set_socketio(sio):
    global socketio_instance
    socketio_instance = sio
    logger.info("[AGENT-CORE] SocketIO registered")


class BaseAgent(ABC):
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.agent_id = str(uuid.uuid4())[:8]
        self.name = name
        self.config = config or {}
        self.role = self.config.get('role', 'generalist')
        self.capabilities = self.config.get('capabilities', [])
        self.goal = self.config.get('goal', '')

        self.state: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}
        self.short_term_memory: List[Dict] = []
        self.working_memory: Dict[str, Any] = {}
        self.memory_limit = self.config.get('memory_limit', 50)

        self.tools = {}
        self.tool_registry = None
        self._register_tools()

        self.groq_key = os.getenv('GROQ_API_KEY')
        self.llm_model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
        self.llm_max_tokens = int(os.getenv('GROQ_MAX_TOKENS', 2000))
        self.llm_temperature = float(os.getenv('GROQ_TEMPERATURE', 0.3))

        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metrics = {
            'tasks_processed': 0, 'success_count': 0, 'error_count': 0,
            'fix_count': 0, 'avg_response_time': 0.0,
            'total_llm_calls': 0, 'total_tool_calls': 0,
        }

        self.history: List[Dict] = []
        self.history_limit = 100
        self.is_busy = False
        self.max_retries = self.config.get('max_retries', 3)

        try:
            from .tools.tool_registry import create_agent_toolset
            self.tool_registry = create_agent_toolset(self)
            print(f"[{self.name}] Tool registry loaded with {len(self.tool_registry.list_tools())} tools")
        except Exception as e:
            print(f"[{self.name}] Tool registry failed: {e}")
            self.tool_registry = None

    def _agent_key(self) -> str:
        n = self.name.lower()
        for suffix in ['_agent', 'agent', ' ']:
            n = n.replace(suffix, '')
        return n.strip() or 'agent'

    def _emit_agent_event(self, action, success, confidence=0.7, extra=None):
        agent_key = self._agent_key()
        action_str = str(action or '')
        try:
            emit_event(f'{agent_key}:action', {
                'agent': self.name, 'agent_id': self.agent_id,
                'action': action_str or agent_key,
                'success': bool(success), 'extra': extra or {},
            })
        except Exception: pass

        try:
            feats = [float(stable_hash(agent_key)), float(stable_hash(action_str)),
                     0.0, 0.0, 0.0, 0.0, 0.0, float(int(time.time() / 3600) % 24)]
            _ml_log(tool=f'{agent_key}:{action_str or "task"}',
                    features=feats, success=bool(success), confidence=float(confidence))
        except Exception: pass

    # ⭐ NOTIFICATION DISPATCH — for EVERY agent
    def _send_notification(self, result, input_data, context, elapsed):
        if not context: return
        user_id = context.get('user_id')
        if not user_id:
            print(f"[{self.name}] ⏸️ No user_id — skip notification")
            return

        agent_key = self._agent_key()
        success = result.get('success', True) if isinstance(result, dict) else True
        duration = f"{elapsed:.1f}s"

        print(f"[{self.name}] 🔔 Notification (agent={agent_key}, success={success})")

        try:
            from services.notification_service import (
                notify_deploy, notify_security, notify_pipeline,
                notify_code_fix, notify_monitor, notify_scale,
                notify_agent_action,
            )

            if agent_key == 'deploy':
                repo_url = input_data.get('repo_url', 'N/A') if isinstance(input_data, dict) else 'N/A'
                project_name = ((input_data.get('project_name') if isinstance(input_data, dict) else None)
                                or result.get('project_name') or 'app')
                notify_deploy(user_id, repo_url, project_name, result, duration)

            elif agent_key == 'security':
                notify_security(user_id, result.get('owner', 'N/A'), result.get('repo', 'N/A'), result)

            elif agent_key == 'pipeline':
                repo_url = input_data.get('repo_url', 'N/A') if isinstance(input_data, dict) else 'N/A'
                project_name = result.get('project_name') or 'pipeline'
                notify_pipeline(user_id, repo_url, project_name, result, duration)

            elif agent_key == 'code_fixer':
                notify_code_fix(user_id, result, duration)

            elif agent_key == 'monitor':
                url = ''
                if isinstance(input_data, dict):
                    urls = input_data.get('urls', [])
                    url = urls[0] if urls else (input_data.get('url') or 'N/A')
                notify_monitor(user_id, url, result)

            elif agent_key == 'scale':
                service = ((input_data.get('service') if isinstance(input_data, dict) else None)
                           or result.get('service') or 'app')
                notify_scale(user_id, service, result)

            else:
                action = ''
                if isinstance(input_data, dict):
                    action = input_data.get('action', '') or input_data.get('query', '')
                notify_agent_action(user_id, self.name, str(action)[:80] or 'task',
                                    success, result, duration)

        except Exception as e:
            logger.warning(f"[{self.name}] Notification failed: {e}")

    @abstractmethod
    def process(self, input_data, context=None) -> Dict: pass

    def _register_tools(self): pass

    def register_tool(self, name, func, description=''):
        self.tools[name] = {'name': name, 'func': func, 'description': description}

    def use_tool(self, name, **kwargs) -> Dict:
        self.metrics['total_tool_calls'] += 1
        if name in self.tools:
            try:
                result = self.tools[name]['func'](**kwargs)
                return result if isinstance(result, dict) else {'success': True, 'result': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        if self.tool_registry:
            return self.tool_registry.execute(name, **kwargs)
        return {'success': False, 'error': f'Tool not found: {name}'}

    def list_tools(self) -> List[str]:
        tools = list(self.tools.keys())
        if self.tool_registry:
            tools.extend(self.tool_registry.list_tools())
        return list(set(tools))

    def call_llm(self, prompt, system_prompt=None, expect_json=False,
                 temperature=None, max_tokens=None, retry_on_error=True):
        if not self.groq_key:
            self.emit_log("GROQ_API_KEY not set", "error")
            return None
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            kwargs = {
                'model': self.llm_model, 'messages': messages,
                'temperature': temperature if temperature is not None else self.llm_temperature,
                'max_tokens': max_tokens if max_tokens is not None else self.llm_max_tokens,
            }
            if expect_json:
                kwargs['response_format'] = {'type': 'json_object'}
            response = client.chat.completions.create(**kwargs)
            self.metrics['total_llm_calls'] += 1
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            self.emit_log(f"LLM failed: {error_msg[:150]}", "error")
            if retry_on_error and ('413' in error_msg or 'rate_limit' in error_msg.lower()):
                return self.call_llm(prompt[:1500], system_prompt, expect_json,
                                     temperature, max_tokens=1500, retry_on_error=False)
            return None

    def think(self, prompt, context=None):
        system_prompt = (f"You are {self.name}, {self.role}. Goal: {self.goal}\n"
                         f"Tools: {', '.join(self.list_tools()[:15])}\n"
                         "Think step-by-step. Be concise.")
        return self.call_llm(prompt, system_prompt)

    def reflect(self, action, result, error=None):
        prompt = f"Action: {action}\nResult: {json.dumps(result, default=str)[:500]}\n"
        if error: prompt += f"Error: {error}\n"
        prompt += '\nReflect: {"success": true/false, "root_cause": "...", "fix_suggestion": "...", "confidence": 0.0-1.0}'
        response = self.call_llm(prompt, expect_json=True)
        if not response: return {'success': False, 'root_cause': 'failed', 'confidence': 0.0}
        try: return json.loads(response)
        except: return {'success': False, 'root_cause': 'invalid', 'confidence': 0.0}

    def add_memory(self, item):
        item['timestamp'] = datetime.now().isoformat()
        self.short_term_memory.append(item)
        if len(self.short_term_memory) > self.memory_limit:
            self.short_term_memory = self.short_term_memory[-self.memory_limit:]

    def remember(self, key, value):
        self.working_memory[key] = {'value': value, 'timestamp': datetime.now().isoformat()}

    def recall(self, key):
        item = self.working_memory.get(key)
        return item['value'] if item else None

    def clear_working_memory(self): self.working_memory = {}

    def update_state(self, key, value):
        self.state[key] = value
        self.last_activity = datetime.now()

    def get_state(self, key=None):
        return self.state.get(key) if key else self.state

    def set_context(self, context):
        if context: self.context.update(context)

    def emit_log(self, message, level='info', sid=None):
        self.log_activity(message, level)
        if socketio_instance:
            payload = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'agent': self.name, 'agent_id': self.agent_id,
                'message': message, 'level': level,
            }
            try:
                if sid:
                    socketio_instance.emit('agent_log', payload, room=sid)
                    socketio_instance.emit('live_log', payload, room=sid)
                else:
                    socketio_instance.emit('agent_log', payload)
                    socketio_instance.emit('live_log', payload)
            except Exception: pass

    def log_activity(self, message, level='info', data=None):
        entry = {'timestamp': datetime.now().isoformat(), 'agent': self.name,
                 'agent_id': self.agent_id, 'level': level,
                 'message': message, 'data': data or {}}
        self.history.append(entry)
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]
        self.last_activity = datetime.now()
        if level == 'info': logger.info(f"[{self.name}] {message}")
        elif level in ('warning', 'warn'): logger.warning(f"[{self.name}] {message}")
        elif level in ('error', 'critical'): logger.error(f"[{self.name}] {message}")
        elif level == 'success': logger.info(f"[{self.name}] OK {message}")

    def track_metric(self, success, response_time):
        self.metrics['tasks_processed'] += 1
        if success: self.metrics['success_count'] += 1
        else: self.metrics['error_count'] += 1
        total = self.metrics['tasks_processed']
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total

    def get_metrics(self):
        total = self.metrics['tasks_processed']
        return {**self.metrics,
                'success_rate': (self.metrics['success_count'] / total * 100) if total > 0 else 0,
                'uptime_seconds': (datetime.now() - self.created_at).total_seconds()}

    def retry_with_reflection(self, action_fn, action_name, max_retries=None, sid=None):
        max_retries = max_retries or self.max_retries
        last_error = None
        for attempt in range(1, max_retries + 1):
            self.emit_log(f"Retry [{action_name}] {attempt}/{max_retries}", "info", sid)
            try:
                result = action_fn()
                if isinstance(result, dict) and result.get('success'):
                    self.metrics['fix_count'] += (1 if attempt > 1 else 0)
                    return result
                last_error = result.get('error', 'Unknown') if isinstance(result, dict) else str(result)
            except Exception as e:
                last_error = str(e)
                traceback.print_exc()
            if attempt < max_retries:
                self.reflect(action_name, {'attempt': attempt}, last_error)
        return {'success': False, 'error': f'Failed after {max_retries}: {last_error}'}

    def delegate_to_agent(self, agent, task, context=None):
        action = task.get('action', 'unknown')
        agent_key = agent._agent_key() if hasattr(agent, '_agent_key') else agent.name.lower()
        self.emit_log(f"Delegating to {agent.name}: {action}", "info")
        try:
            emit_event(f'{agent_key}:delegation_started',
                       {'from': self.name, 'to': agent.name, 'action': action})
        except Exception: pass
        try:
            result = agent.safe_process(task, context or {})
            success = result.get('success', True) if isinstance(result, dict) else True
            self.add_memory({'type': 'delegation', 'to': agent.name,
                             'task': action, 'result': 'success' if success else 'failed'})
            try:
                emit_event(f'{agent_key}:delegation_completed',
                           {'from': self.name, 'to': agent.name, 'action': action, 'success': success})
            except Exception: pass
            return result
        except Exception as e:
            self.emit_log(f"Delegation failed: {str(e)[:100]}", "error")
            return {'success': False, 'error': str(e)}

    def to_dict(self):
        return {'agent_id': self.agent_id, 'name': self.name, 'role': self.role,
                'goal': self.goal, 'state': self.state, 'metrics': self.get_metrics(),
                'tools': self.list_tools(), 'history': self.history[-20:],
                'created_at': self.created_at.isoformat()}

    def safe_process(self, input_data, context=None):
        start = time.time()
        self.is_busy = True
        self.emit_log(f"Starting: {str(input_data)[:80]}", "info")
        try:
            result = self.process(input_data, context)
            elapsed = time.time() - start
            success = result.get('success', True) if isinstance(result, dict) else True
            self.track_metric(success, elapsed)
            self.emit_log(f"Completed in {elapsed:.2f}s",
                          "success" if success else "warning")
            action = ''
            if isinstance(input_data, dict):
                action = input_data.get('action', '') or input_data.get('query', '')
            self._emit_agent_event(action=str(action)[:60], success=success, confidence=0.7,
                                   extra={'duration': round(elapsed, 2)})
            # ⭐ Send notification
            try: self._send_notification(result, input_data, context, elapsed)
            except Exception as e: logger.warning(f"[{self.name}] Notify failed: {e}")
            return result
        except Exception as e:
            elapsed = time.time() - start
            self.track_metric(False, elapsed)
            self.emit_log(f"Fatal: {str(e)[:150]}", "error")
            traceback.print_exc()
            self._emit_agent_event(action='error', success=False, confidence=0.3,
                                   extra={'error': str(e)[:200]})
            return {'success': False, 'error': str(e)}
        finally:
            self.is_busy = False