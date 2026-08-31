import json
import re
import uuid
import time
from datetime import datetime
from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for planning DevOps workflows and emitting live logs"""
    
    def __init__(self, config=None):
        super().__init__('PlannerAgent', config)
        self.templates = self._load_templates()
    
    def _load_templates(self):
        """Load standard DevOps execution templates"""
        return {
            'deployment': {
                'steps': [
                    'Analyze application structure',
                    'Build Docker container image',
                    'Push image to registry',
                    'Configure Kubernetes manifests',
                    'Apply deployment manifests to cluster',
                    'Verify service health and routing'
                ],
                'estimated_time': '3-5 minutes',
                'rollback_strategy': 'Automated Rollback to previous deployment'
            },
            'ci_cd': {
                'steps': [
                    'Checkout source code',
                    'Install package dependencies',
                    'Run unit & integration test suites',
                    'Package application artifacts',
                    'Deploy build target to environment'
                ],
                'estimated_time': '5-10 minutes',
                'rollback_strategy': 'Revert to stable git commit tag'
            },
            'infrastructure': {
                'steps': [
                    'Parse Infrastructure-as-Code definitions',
                    'Validate cloud config files',
                    'Generate execution plan',
                    'Apply infrastructure changes',
                    'Verify state store consistency'
                ],
                'estimated_time': '4-8 minutes',
                'rollback_strategy': 'Restore state file from backup'
            }
        }
    
    def process(self, input_data, context=None):
        """Process planning requests with live step-by-step logs"""
        sid = context.get('sid') if context else None
        
        input_text = input_data.get('command', input_data) if isinstance(input_data, dict) else str(input_data)
        self.emit_log(f"📋 Planner Agent analyzing request: '{input_text}'", "info", sid)
        
        task_type = self._detect_task_type(input_text)
        self.emit_log(f"Identified Workflow Strategy: [{task_type.upper()}]", "info", sid)
        
        template = self.templates.get(task_type, self.templates['deployment'])
        plan = self._create_plan(input_text, task_type, template, context, sid)
        
        self.emit_log(f"✅ Generated execution plan #{plan['id']} with {len(plan['steps'])} steps.", "success", sid)
        
        return {
            'success': True,
            'task_type': task_type,
            'plan': plan,
            'estimated_time': template.get('estimated_time'),
            'rollback_strategy': template.get('rollback_strategy')
        }
    
    def _detect_task_type(self, text_data):
        """Identify task type based on keywords"""
        text = text_data.lower()
        if any(w in text for w in ['deploy', 'deployment', 'release', 'publish']):
            return 'deployment'
        elif any(w in text for w in ['pipeline', 'ci', 'cd', 'build', 'test']):
            return 'ci_cd'
        elif any(w in text for w in ['infra', 'terraform', 'cloud', 'aws', 'k8s']):
            return 'infrastructure'
        return 'deployment'
    
    def _create_plan(self, input_data, task_type, template, context, sid=None):
        """Construct detailed step plan with enriched details"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        plan = {
            'id': plan_id,
            'type': task_type,
            'steps': [],
            'created_at': datetime.now().isoformat(),
            'context': context or {}
        }
        
        for i, step in enumerate(template['steps']):
            enriched_step = {
                'id': f"step_{i+1}",
                'name': step,
                'status': 'pending',
                'order': i + 1,
                'details': self._enrich_step(step, input_data)
            }
            plan['steps'].append(enriched_step)
            self.emit_log(f"  Step {i+1}: {step}", "info", sid)
            time.sleep(0.1)
        
        return plan
    
    def _enrich_step(self, step, input_data):
        """Enrich each step with execution commands"""
        enriched = {
            'description': step,
            'estimated_duration': self._estimate_duration(step)
        }
        
        step_lower = step.lower()
        if 'docker' in step_lower:
            enriched['command'] = 'docker build -t app:latest .'
        elif 'kubernetes' in step_lower or 'manifest' in step_lower:
            enriched['command'] = 'kubectl apply -f k8s/'
        elif 'terraform' in step_lower:
            enriched['command'] = 'terraform apply -auto-approve'
        
        return enriched
    
    def _estimate_duration(self, step):
        """Provide estimated step durations"""
        durations = {
            'docker': '120s',
            'kubernetes': '60s',
            'terraform': '90s',
            'test': '180s',
            'build': '240s',
            'deploy': '120s'
        }
        for key, duration in durations.items():
            if key in step.lower():
                return duration
        return "60s"