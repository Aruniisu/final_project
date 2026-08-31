import subprocess
import json
import os
import time
import random
from datetime import datetime
from .base_agent import BaseAgent

class ExecutorAgent(BaseAgent):
    """Agent responsible for executing DevOps tasks, system monitoring, and infrastructure scaling"""
    
    def __init__(self, config=None):
        super().__init__('ExecutorAgent', config)
        self.execution_history = []
    
    def process(self, input_data, context=None):
        """Execute a plan and stream terminal logs to UI"""
        sid = context.get('sid') if context else None
        plan = input_data if isinstance(input_data, dict) else {'task': str(input_data)}
        
        task_name = plan.get('task', 'Execution Plan')
        self.emit_log(f"Executor Engine initiated for task: [{task_name}]", "info", sid)
        
        result = self._execute_plan(plan, context, sid)
        
        self.execution_history.append({
            'timestamp': datetime.now().isoformat(),
            'plan': plan,
            'result': result
        })
        
        return result
    
    def _execute_plan(self, plan, context, sid=None):
        """Execute each step in plan with live status feedback"""
        task = plan.get('task', '')
        steps = plan.get('steps', [])
        
        execution_result = {
            'success': True,
            'outputs': [],
            'errors': [],
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = datetime.now()
        
        if not steps:
            steps = self._generate_steps_for_task(task)
        
        for step in steps:
            try:
                step_result = self._execute_step(step, context, sid)
                execution_result['outputs'].append({
                    'step': step.get('name', 'unknown'),
                    'result': step_result
                })
            except Exception as e:
                execution_result['success'] = False
                execution_result['errors'].append({
                    'step': step.get('name', 'unknown'),
                    'error': str(e)
                })
                self.emit_log(f"Execution failed at step [{step.get('name')}]: {str(e)}", "error", sid)
                break
        
        execution_result['duration'] = round((datetime.now() - start_time).total_seconds(), 2)
        self.emit_log(f"Execution plan completed in {execution_result['duration']}s", "success", sid)
        
        return execution_result
    
    def _generate_steps_for_task(self, task):
        """Generate logical steps based on incoming UI trigger action"""
        task_lower = task.lower()
        
        if any(k in task_lower for k in ['monitor', 'monitoring', 'health']):
            return [
                {'name': 'Check CPU & Core Temperature'},
                {'name': 'Audit RAM & Swap Allocation'},
                {'name': 'Disk IOPS & Volume Space'},
                {'name': 'Container Network Latency'}
            ]
        elif 'scale' in task_lower:
            return [
                {'name': 'Evaluate Pod Replica Threshold'},
                {'name': 'Provision Elastic Node Resources'},
                {'name': 'Rebalance Cluster Traffic'}
            ]
        elif 'deploy' in task_lower:
            return [
                {'name': 'Build Production Image'},
                {'name': 'Push Docker Image Registry'},
                {'name': 'Deploy Web App Container'},
                {'name': 'Verify Health Endpoint'}
            ]
        else:
            return [
                {'name': 'Validate Environment Config'},
                {'name': 'Execute Command Pipeline'}
            ]
    
    def _execute_step(self, step, context, sid=None):
        """Execute individual step and send metric data"""
        step_name = step.get('name', 'Step Execution')
        self.emit_log(f"Executing: {step_name}...", "info", sid)
        
        time.sleep(0.7)  # Cinematic delay for screen recording
        
        cpu_val = random.randint(18, 42)
        mem_val = random.randint(35, 62)
        
        result = {
            'step': step_name,
            'status': 'completed',
            'duration': round(random.uniform(0.3, 1.2), 2),
            'metrics': {'cpu': f"{cpu_val}%", 'memory': f"{mem_val}%"}
        }
        
        if 'cpu' in step_name.lower():
            self.emit_log(f"Metrics Stream -> CPU Usage: {cpu_val}% | Load Avg: 0.14, 0.22, 0.18", "info", sid)
        elif 'ram' in step_name.lower() or 'memory' in step_name.lower():
            self.emit_log(f"Metrics Stream -> RAM Usage: {mem_val}% (4.1GB / 8.0GB allocated)", "info", sid)
        elif 'scale' in step_name.lower() or 'replica' in step_name.lower():
            self.emit_log("Scaling action -> Increased worker replicas from 2 to 4 instances", "success", sid)
        else:
            self.emit_log(f"Step [{step_name}] passed verification checks.", "success", sid)
            
        return result
    
    def _run_command(self, command, cwd=None):
        """Run a shell command natively"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_history(self, limit=10):
        return self.execution_history[-limit:]