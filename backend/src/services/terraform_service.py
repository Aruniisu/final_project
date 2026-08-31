import os
import subprocess
import json
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TerraformService:
    """Service for interacting with Terraform"""
    
    def __init__(self, working_dir=None):
        self.working_dir = working_dir or os.getcwd()
        self._check_terraform()
    
    def _check_terraform(self):
        """Check if Terraform is installed"""
        try:
            result = subprocess.run(['terraform', '--version'], capture_output=True, text=True)
            self.installed = result.returncode == 0
            if self.installed:
                self.version = result.stdout.split('\n')[0]
        except FileNotFoundError:
            self.installed = False
    
    def is_installed(self):
        """Check if Terraform is installed"""
        return self.installed
    
    def get_version(self):
        """Get Terraform version"""
        if not self.installed:
            return None
        return self.version
    
    def init(self, directory=None):
        """Initialize Terraform"""
        directory = directory or self.working_dir
        try:
            result = subprocess.run(
                ['terraform', 'init'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            logger.error(f"Terraform init error: {e}")
            return {'success': False, 'error': str(e)}
    
    def plan(self, directory=None, var_file=None):
        """Create Terraform plan"""
        directory = directory or self.working_dir
        try:
            cmd = ['terraform', 'plan', '-json']
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True
            )
            
            # Parse plan output
            try:
                plan_json = json.loads(result.stdout)
                return {
                    'success': result.returncode == 0,
                    'plan': plan_json,
                    'raw': result.stdout
                }
            except json.JSONDecodeError:
                return {
                    'success': result.returncode == 0,
                    'plan': None,
                    'raw': result.stdout,
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"Terraform plan error: {e}")
            return {'success': False, 'error': str(e)}
    
    def apply(self, directory=None, var_file=None, auto_approve=True):
        """Apply Terraform plan"""
        directory = directory or self.working_dir
        try:
            cmd = ['terraform', 'apply', '-json']
            if auto_approve:
                cmd.append('-auto-approve')
            if var_file:
                cmd.extend(['-var-file', var_file])
            
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True
            )
            
            # Parse output
            try:
                apply_json = json.loads(result.stdout)
                return {
                    'success': result.returncode == 0,
                    'result': apply_json,
                    'raw': result.stdout
                }
            except json.JSONDecodeError:
                return {
                    'success': result.returncode == 0,
                    'result': None,
                    'raw': result.stdout,
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"Terraform apply error: {e}")
            return {'success': False, 'error': str(e)}
    
    def destroy(self, directory=None, auto_approve=True):
        """Destroy Terraform resources"""
        directory = directory or self.working_dir
        try:
            cmd = ['terraform', 'destroy', '-json']
            if auto_approve:
                cmd.append('-auto-approve')
            
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True
            )
            
            try:
                destroy_json = json.loads(result.stdout)
                return {
                    'success': result.returncode == 0,
                    'result': destroy_json,
                    'raw': result.stdout
                }
            except json.JSONDecodeError:
                return {
                    'success': result.returncode == 0,
                    'result': None,
                    'raw': result.stdout,
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"Terraform destroy error: {e}")
            return {'success': False, 'error': str(e)}
    
    def output(self, directory=None):
        """Get Terraform outputs"""
        directory = directory or self.working_dir
        try:
            result = subprocess.run(
                ['terraform', 'output', '-json'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {'error': result.stderr}
        except Exception as e:
            logger.error(f"Terraform output error: {e}")
            return {'error': str(e)}
    
    def generate_config(self, provider, resources):
        """Generate Terraform configuration"""
        config = f"""
terraform {{
  required_providers {{
    {provider} = {{
      source = "hashicorp/{provider}"
      version = "~> 4.0"
    }}
  }}
}}

provider "{provider}" {{
  region = "us-west-2"
}}

"""
        for resource in resources:
            config += f"""
resource "{resource['type']}" "{resource['name']}" {{
"""
            for key, value in resource.get('attributes', {}).items():
                if isinstance(value, str):
                    config += f'  {key} = "{value}"\n'
                elif isinstance(value, dict):
                    config += f'  {key} = {json.dumps(value, indent=2)}\n'
                else:
                    config += f'  {key} = {value}\n'
            config += "}\n"
        
        return config
    
    def save_config(self, content, filename='main.tf', directory=None):
        """Save Terraform configuration to file"""
        directory = directory or self.working_dir
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def validate(self, directory=None):
        """Validate Terraform configuration"""
        directory = directory or self.working_dir
        try:
            result = subprocess.run(
                ['terraform', 'validate'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            logger.error(f"Terraform validate error: {e}")
            return {'success': False, 'error': str(e)}
    
    def format(self, directory=None):
        """Format Terraform files"""
        directory = directory or self.working_dir
        try:
            result = subprocess.run(
                ['terraform', 'fmt'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            logger.error(f"Terraform fmt error: {e}")
            return {'success': False, 'error': str(e)}