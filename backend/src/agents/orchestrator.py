import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base_agent import BaseAgent
from .cicd_agent import CICDAgent
from .infra_agent import InfraAgent
from .self_healing_agent import SelfHealingAgent
from .analyzer_agent import AnalyzerAgent

class Orchestrator(BaseAgent):
    """The Brain - Orchestrates all sub-agents, tasks, and real-time Socket.IO logs"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__('Orchestrator', config)
        self.agents = {
            'cicd': CICDAgent(config),
            'infra': InfraAgent(config),
            'self_healing': SelfHealingAgent(config),
            'analyzer': AnalyzerAgent(config)
        }
        self.task_queue = []
        self.active_executions = {}
    
    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        """Main entry point - processes incoming inputs and routes to specialized sub-agents"""
        sid = context.get('sid') if context else None
        
        preview_text = str(input_data)[:80] if not isinstance(input_data, dict) else json.dumps(input_data)[:80]
        self.emit_log(f"🧠 Orchestrator received event payload: {preview_text}...", "info", sid)
        
        input_type = self._classify_input(input_data)
        self.emit_log(f"Detected event intent classification: [{input_type.upper()}]", "info", sid)
        
        if input_type == 'file_upload':
            return self._handle_file_upload(input_data, context, sid)
        elif input_type == 'devops_command':
            return self._handle_devops_command(input_data, context, sid)
        elif input_type == 'webhook':
            return self._handle_webhook(input_data, context, sid)
        elif input_type == 'natural_language':
            return self._handle_natural_language(input_data, context, sid)
        else:
            return self._handle_general(input_data, context, sid)
    
    def _classify_input(self, input_data: Any) -> str:
        """Classify input type into specific action buckets"""
        if isinstance(input_data, dict):
            if 'files' in input_data or 'file' in input_data:
                return 'file_upload'
            if 'webhook' in input_data or 'repository' in input_data:
                return 'webhook'
            if 'command' in input_data or 'action' in input_data:
                # If command is chat prompt, classify as natural language
                if input_data.get('action') == 'chat' or 'query' in input_data:
                    return 'natural_language'
                return 'devops_command'
        
        if isinstance(input_data, str):
            if input_data.startswith('{'):
                try:
                    json.loads(input_data)
                    return 'devops_command'
                except Exception:
                    pass
            return 'natural_language'
        
        return 'general'
    
    def _handle_file_upload(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        """Analyze project files and trigger automated dockerization"""
        files = input_data.get('files', [])
        project_name = input_data.get('project_name', 'devops-app')
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.emit_log(f"Processing project folder [{project_name}] with {len(files)} files...", "info", sid)
        
        analyzer_result = self.agents['analyzer'].process({'files': files, 'action': 'analyze'}, context)
        project_type = self._detect_project_type(files)
        
        self.emit_log(f"Code Analysis Result: Language Target -> {project_type.upper()}", "success", sid)
        
        infra_result = None
        if project_type != 'unknown':
            self.emit_log("Delegating Dockerfile generation to Infra Agent...", "info", sid)
            infra_result = self.agents['infra'].process({
                'project_type': project_type,
                'files': files,
                'action': 'generate'
            }, context)
        
        result = {
            'execution_id': execution_id,
            'status': 'analyzed',
            'project_name': project_name,
            'project_type': project_type,
            'analysis': analyzer_result,
            'infrastructure': infra_result,
            'files': files,
            'timestamp': datetime.now().isoformat()
        }
        
        self.active_executions[execution_id] = result
        return result
    
    def _handle_devops_command(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        """Route DevOps control actions to target sub-agent"""
        command = str(input_data.get('command', input_data.get('query', '')))
        action = str(input_data.get('action', ''))
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if 'deploy' in command.lower() or action == 'deploy':
            return self._execute_deploy(execution_id, input_data, context, sid)
        elif 'pipeline' in command.lower() or action == 'pipeline':
            return self._execute_pipeline(execution_id, input_data, context, sid)
        elif 'fix' in command.lower() or action == 'fix':
            return self._execute_fix(execution_id, input_data, context, sid)
        elif 'analyze' in command.lower() or action == 'analyze':
            return self._execute_analyze(execution_id, input_data, context, sid)
        elif 'scale' in command.lower() or action == 'scale':
            return self._execute_scale(execution_id, input_data, context, sid)
        else:
            return self._execute_general(execution_id, input_data, context, sid)
    
    def _handle_webhook(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        """Handle incoming VCS Webhooks"""
        self.emit_log("Git Push Webhook Received! Handing off to CI/CD Engine...", "info", sid)
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = self.agents['cicd'].process({
            'event_type': input_data.get('event_type', 'push'),
            'repository': input_data.get('repository', {}),
            'commits': input_data.get('commits', []),
            'action': 'trigger_pipeline'
        }, context)
        
        result['execution_id'] = execution_id
        self.active_executions[execution_id] = result
        return result
    
    def _handle_natural_language(self, input_data: Any, context: Dict, sid: Optional[str] = None) -> Dict:
        """Parse natural language command intent and execute dynamic logic"""
        if isinstance(input_data, dict):
            text = input_data.get('query', input_data.get('command', ''))
        else:
            text = str(input_data)
            
        intent = self._parse_intent(text)
        self.emit_log(f"Parsed NLP Intent: '{intent}' from user request.", "info", sid)
        
        # Check for Dockerfile / Infra generation request
        if "dockerfile" in text.lower() or "docker" in text.lower():
            self.emit_log("Delegating Dockerfile generation request to Infra Agent...", "info", sid)
            
            # Detect target language from text
            lang = 'python'
            if 'node' in text.lower() or 'js' in text.lower():
                lang = 'nodejs'
            elif 'java' in text.lower():
                lang = 'java'
            elif 'go' in text.lower():
                lang = 'go'
                
            infra_res = self.agents['infra'].process({'action': 'generate', 'project_type': lang}, context)
            
            # Formatting response safely
            docker_content = infra_res.get('dockerfile', infra_res.get('response', ''))
            
            response_msg = (
                f"Here is the generated Dockerfile for your {lang.upper()} application:\n\n"
                f"```dockerfile\n{docker_content}\n```\n\n"
                f"💡 *Optional: You can also upload your project files anytime using the Upload button to automate this process!*"
            )
            return {
                'status': 'completed',
                'response': response_msg,
                'infra': infra_res
            }
            
        if intent != 'general':
            return self._handle_devops_command({'command': text, 'action': intent}, context, sid)
        else:
            return self._execute_general(f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}", {'command': text}, context, sid)
    
    def _parse_intent(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ['deploy', 'deployment', 'release', 'publish']):
            return 'deploy'
        elif any(w in text_lower for w in ['pipeline', 'ci', 'cd', 'build']):
            return 'pipeline'
        elif any(w in text_lower for w in ['fix', 'repair', 'debug', 'error', 'heal']):
            return 'fix'
        elif any(w in text_lower for w in ['analyze', 'scan', 'inspect']):
            return 'analyze'
        elif any(w in text_lower for w in ['scale', 'scaling', 'replica']):
            return 'scale'
        return 'general'
    
    def _execute_deploy(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Orchestrator pipeline stage: DEPLOYMENT", "info", sid)
        infra_result = self.agents['infra'].process({'action': 'deploy'}, context)
        cicd_result = self.agents['cicd'].process({'action': 'deploy'}, context)
        
        return {
            'execution_id': execution_id,
            'type': 'deploy',
            'status': 'completed',
            'infra': infra_result,
            'deployment': cicd_result,
            'url': cicd_result.get('url', 'http://localhost:8080'),
            'timestamp': datetime.now().isoformat(),
            'response': "🚀 Deployment triggered successfully! Your project is being built and deployed."
        }
    
    def _execute_pipeline(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Orchestrator pipeline stage: PIPELINE CREATION", "info", sid)
        result = self.agents['cicd'].process({'action': 'create_pipeline', 'command': input_data.get('command', '')}, context)
        return {
            'execution_id': execution_id, 
            'type': 'pipeline', 
            'status': 'completed', 
            'pipeline': result,
            'response': "⚙️ CI/CD Pipeline configuration generated successfully."
        }
    
    def _execute_fix(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Orchestrator pipeline stage: SELF-HEALING FIX", "info", sid)
        result = self.agents['self_healing'].process({'action': 'fix', 'command': input_data.get('command', '')}, context)
        return {
            'execution_id': execution_id, 
            'type': 'fix', 
            'status': 'completed', 
            'result': result,
            'response': "🔧 Self-healing agent has analyzed and fixed issues in your code."
        }
    
    def _execute_analyze(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Orchestrator pipeline stage: CODE ANALYSIS", "info", sid)
        result = self.agents['analyzer'].process({'action': 'analyze', 'command': input_data.get('command', '')}, context)
        return {
            'execution_id': execution_id, 
            'type': 'analyze', 
            'status': 'completed', 
            'analysis': result,
            'response': "🔍 Code security analysis completed successfully."
        }
    
    def _execute_scale(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Orchestrator pipeline stage: INFRA SCALING", "info", sid)
        result = self.agents['infra'].process({'action': 'scale', 'replicas': input_data.get('replicas', 5)}, context)
        return {
            'execution_id': execution_id, 
            'type': 'scale', 
            'status': 'completed', 
            'scaling': result,
            'response': "📊 Infrastructure scaled to requested replicas successfully."
        }
    
    def _execute_general(self, execution_id: str, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Executing fallback general request handling...", "info", sid)
        cmd = input_data.get('command', input_data.get('query', ''))
        return {
            'execution_id': execution_id,
            'type': 'general',
            'status': 'completed',
            'response': f"Processed instruction: '{cmd}'. AI Assistant is ready for your next request!"
        }
    
    def _handle_general(self, input_data: Any, context: Dict, sid: Optional[str] = None) -> Dict:
        return self._execute_general(f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}", {'command': str(input_data)}, context, sid)
    
    def _detect_project_type(self, files: List[Dict]) -> str:
        file_names = [f.get('name', '') for f in files]
        if any('package.json' in f for f in file_names):
            return 'nodejs'
        elif any('requirements.txt' in f for f in file_names):
            return 'python'
        elif any('pom.xml' in f for f in file_names):
            return 'java'
        elif any('Dockerfile' in f for f in file_names):
            return 'docker'
        elif any(f.endswith('.py') for f in file_names):
            return 'python'
        elif any(f.endswith('.js') or f.endswith('.jsx') for f in file_names):
            return 'javascript'
        return 'unknown'
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        return self.active_executions.get(execution_id)
    
    def get_all_executions(self) -> List[Dict]:
        return list(self.active_executions.values())
    
    def get_agent_status(self) -> Dict:
        return {
            'orchestrator': self.to_dict(),
            'agents': {name: agent.to_dict() for name, agent in self.agents.items()}
        }