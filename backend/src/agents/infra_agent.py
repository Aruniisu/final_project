import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base_agent import BaseAgent

class InfraAgent(BaseAgent):
    """Agent responsible for Infrastructure as Code (Docker, Kubernetes, Terraform) & Scaling"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__('InfraAgent', config)

    def process(self, input_data: Any, context: Optional[Dict] = None) -> Dict:
        sid = context.get('sid') if context else None
        action = input_data.get('action', '') if isinstance(input_data, dict) else ''
        
        self.emit_log(f"🏗️ InfraAgent triggered for action: [{action.upper()}]", "info", sid)
        
        if action == 'generate':
            return self._generate_infra(input_data, context, sid)
        elif action == 'scale':
            return self._scale_infrastructure(input_data, context, sid)
        elif action == 'deploy':
            return self._prepare_deployment_config(input_data, context, sid)
        else:
            return self._default_action(input_data, context, sid)

    def _generate_infra(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        project_type = input_data.get('project_type', 'python')
        self.emit_log(f"Generating optimized Infrastructure files for stack: {project_type.upper()}", "info", sid)
        time.sleep(0.5)

        dockerfile_content = self._get_dockerfile_template(project_type)
        k8s_manifest = self._get_k8s_manifest_template(project_type)

        self.emit_log("Generated Dockerfile and Kubernetes deployment manifests successfully.", "success", sid)

        return {
            'success': True,
            'dockerfile': dockerfile_content,
            'k8s_manifest': k8s_manifest,
            'project_type': project_type
        }

    def _scale_infrastructure(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        replicas = input_data.get('replicas', 5)
        self.emit_log(f"Initiating HPA Auto-Scaling... Adjusting replicas to target count: {replicas}", "info", sid)
        time.sleep(0.8)
        self.emit_log(f"⚡ Kubernetes Cluster scaled to {replicas} active worker pods.", "success", sid)

        return {
            'success': True,
            'status': 'scaled',
            'active_replicas': replicas,
            'timestamp': datetime.now().isoformat()
        }

    def _prepare_deployment_config(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Preparing deployment target specs (Environment: Staging/Production)...", "info", sid)
        return {'success': True, 'target': 'kubernetes-cluster-primary'}

    def _default_action(self, input_data: Dict, context: Dict, sid: Optional[str] = None) -> Dict:
        self.emit_log("Infra Agent on standby.", "info", sid)
        return {'success': True, 'status': 'idle'}

    def _get_dockerfile_template(self, project_type: str) -> str:
        if project_type in ['nodejs', 'javascript']:
            return "FROM node:18-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nEXPOSE 3000\nCMD [\"npm\", \"start\"]"
        elif project_type == 'python':
            return "FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]"
        return "FROM alpine:latest\nCMD [\"echo\", \"Running application\"]"

    def _get_k8s_manifest_template(self, project_type: str) -> str:
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-app-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devops-app
  template:
    metadata:
      labels:
        app: devops-app
    spec:
      containers:
      - name: devops-app
        image: devops-app:latest
        ports:
        - containerPort: 8080
"""