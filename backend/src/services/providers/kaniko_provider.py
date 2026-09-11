"""
Kaniko Deploy Provider
Builds Docker images inside Kubernetes without Docker daemon.
Best for: Docker-based apps, when you have a Kubernetes cluster.
"""

import os
import re
import time
import json
import tempfile
import subprocess
from typing import Dict, Any, Optional

import requests


class KanikoProvider:
    """Builds and deploys Docker images using Kaniko in Kubernetes."""

    name = 'kaniko'
    display_name = 'Kaniko (Kubernetes)'
    supports = ['docker', 'any']

    def __init__(self):
        from dotenv import load_dotenv
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_path = os.path.join(backend_dir, '.env')
        load_dotenv(env_path, override=True)

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.kubeconfig = os.getenv('KUBECONFIG_PATH')  # Path to kubeconfig
        self.registry = os.getenv('DOCKER_REGISTRY')    # e.g., docker.io/username
        self.registry_user = os.getenv('DOCKER_USERNAME')
        self.registry_pass = os.getenv('DOCKER_PASSWORD')

    def can_deploy(self, stack: Dict[str, Any]) -> bool:
        # Kaniko is universal - can build anything with a Dockerfile
        return True

    def deploy(self, payload: Dict[str, Any], on_log=None) -> Dict[str, Any]:
        repo_url = payload.get('repo_url')
        project_name = payload.get('project_name') or 'my-app'
        default_branch = payload.get('default_branch', 'main')
        root_dir = payload.get('root_dir')

        owner, repo = self._parse_url(repo_url)

        def log(msg, level='info'):
            print(f"[KANIKO] {msg}")
            if on_log:
                on_log(msg, level)

        if not self.kubeconfig or not os.path.exists(self.kubeconfig):
            return {'success': False, 'error': 'KUBECONFIG_PATH not set or file missing'}

        if not self.registry:
            return {'success': False, 'error': 'DOCKER_REGISTRY not set in .env'}

        project_name = self._sanitize_name(project_name)
        image_tag = f'{self.registry}/{project_name}:latest'

        # STEP 1: Clone repo
        log(f'Cloning {owner}/{repo}...', 'info')
        tmp_dir = tempfile.mkdtemp(prefix='kaniko_')

        try:
            clone_url = f'https://{self.github_token}@github.com/{owner}/{repo}.git'
            result = subprocess.run(
                ['git', 'clone', '--depth=1', '--branch', default_branch, clone_url, tmp_dir],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {'success': False, 'error': f'Clone failed: {result.stderr[:200]}'}

            log('Cloned repo', 'success')

            # STEP 2: Ensure Dockerfile exists
            dockerfile_path = os.path.join(tmp_dir, root_dir or '', 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                log('No Dockerfile found. Generating one...', 'warning')
                self._generate_dockerfile(os.path.join(tmp_dir, root_dir or ''), payload.get('stack', {}))
                log('Dockerfile generated', 'success')

            # STEP 3: Build & push image with Kaniko (in Kubernetes)
            log('Building image with Kaniko...', 'info')
            build_result = self._build_with_kaniko(
                tmp_dir, root_dir, image_tag, project_name, on_log=log
            )

            if not build_result.get('success'):
                return {'success': False, 'error': build_result.get('error')}

            log(f'Image pushed: {image_tag}', 'success')

            # STEP 4: Deploy to Kubernetes
            log('Deploying to Kubernetes...', 'info')
            deploy_result = self._deploy_to_k8s(project_name, image_tag, on_log=log)

            if not deploy_result.get('success'):
                return {'success': False, 'error': deploy_result.get('error')}

            live_url = deploy_result.get('live_url')

            return {
                'success': True,
                'status': 'deployed',
                'live_url': live_url,
                'provider': self.name,
                'image': image_tag,
            }

        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _parse_url(self, url: str) -> tuple:
        m = re.match(r'https?://github\.com/([^/]+)/([^/\s\.]+?)(?:\.git)?/?$', url.strip())
        return (m.group(1), m.group(2)) if m else (None, None)

    def _sanitize_name(self, name: str) -> str:
        name = name.lower()
        name = re.sub(r'[^a-z0-9\-]', '-', name)
        name = re.sub(r'-{2,}', '-', name)
        return name.strip('-')[:63]

    def _generate_dockerfile(self, path: str, stack: Dict) -> None:
        """Auto-generate a Dockerfile based on stack."""
        stype = stack.get('type', 'unknown')
        content = ''

        if stype == 'python':
            content = '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
'''
        elif stype == 'node':
            content = '''FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
'''
        else:
            content = '''FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["sh", "-c", "echo Hello from container"]
'''

        with open(os.path.join(path, 'Dockerfile'), 'w') as f:
            f.write(content)

    def _build_with_kaniko(self, tmp_dir: str, root_dir: Optional[str], image_tag: str, job_name: str, on_log=None) -> Dict:
        """Run Kaniko as a Kubernetes Job."""
        context_dir = os.path.join(tmp_dir, root_dir or '')
        dockerfile_path = os.path.join(context_dir, 'Dockerfile')

        # Create a ConfigMap with the Dockerfile + context
        # Simpler approach: use a Kaniko pod that clones the repo itself

        # Simpler: Kaniko pod that clones repo internally
        pod_yaml = f"""
apiVersion: v1
kind: Pod
metadata:
  name: kaniko-{job_name[:40].replace('_', '-')}
spec:
  restartPolicy: Never
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    args:
    - "--dockerfile=Dockerfile"
    - "--context=git://github.com/{self.github_token}@github.com/PLACEHOLDER.git"
    - "--destination={image_tag}"
    - "--verbosity=info"
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: docker-config
    configMap:
      name: docker-config
"""

        # Write pod manifest
        pod_file = os.path.join(tmp_dir, 'kaniko-pod.yaml')
        with open(pod_file, 'w') as f:
            f.write(pod_yaml)

        # Apply pod
        try:
            apply_result = subprocess.run(
                ['kubectl', 'apply', '-f', pod_file],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, 'KUBECONFIG': self.kubeconfig},
            )
            if apply_result.returncode != 0:
                return {'success': False, 'error': f'kubectl apply failed: {apply_result.stderr[:300]}'}

            if on_log:
                on_log('Kaniko pod created, waiting for build...', 'info')

            # Wait for pod
            wait_result = subprocess.run(
                ['kubectl', 'wait', '--for=condition=Ready=False', '--for=condition=PodSucceeded',
                 f'pod/kaniko-{job_name[:40].replace("_", "-")}', '--timeout=600s'],
                capture_output=True, text=True, timeout=620,
                env={**os.environ, 'KUBECONFIG': self.kubeconfig},
            )

            if wait_result.returncode != 0:
                return {'success': False, 'error': f'Kaniko build failed: {wait_result.stderr[:200]}'}

            return {'success': True}

        except FileNotFoundError:
            return {'success': False, 'error': 'kubectl not installed'}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Kaniko build timeout'}

    def _deploy_to_k8s(self, app_name: str, image_tag: str, on_log=None) -> Dict:
        """Create a Kubernetes Deployment + Service."""
        deployment_yaml = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: app
        image: {image_tag}
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}
spec:
  selector:
    app: {app_name}
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
"""
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
            f.write(deployment_yaml)
            yaml_file = f.name

        try:
            result = subprocess.run(
                ['kubectl', 'apply', '-f', yaml_file],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, 'KUBECONFIG': self.kubeconfig},
            )
            if result.returncode != 0:
                return {'success': False, 'error': f'kubectl apply failed: {result.stderr[:300]}'}

            # Wait for external IP
            if on_log:
                on_log('Waiting for external IP...', 'info')

            for _ in range(30):
                time.sleep(10)
                svc_result = subprocess.run(
                    ['kubectl', 'get', 'svc', app_name, '-o', 'jsonpath={.status.loadBalancer.ingress[0].ip}'],
                    capture_output=True, text=True, timeout=30,
                    env={**os.environ, 'KUBECONFIG': self.kubeconfig},
                )
                ip = svc_result.stdout.strip()
                if ip:
                    return {'success': True, 'live_url': f'http://{ip}'}

            return {'success': True, 'live_url': f'http://{app_name}.default.svc.cluster.local'}

        finally:
            try:
                os.unlink(yaml_file)
            except Exception:
                pass