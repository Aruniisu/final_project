import docker
import os
import tarfile
import io
import json
import logging
from docker.errors import APIError, NotFound, ImageNotFound

logger = logging.getLogger(__name__)

class DockerService:
    """Service for interacting with Docker API"""
    
    def __init__(self, docker_host=None):
        self.docker_host = docker_host or os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
        self.client = docker.DockerClient(base_url=self.docker_host)
    
    def is_running(self):
        """Check if Docker is running"""
        try:
            self.client.ping()
            return True
        except APIError:
            return False
    
    def get_version(self):
        """Get Docker version"""
        try:
            version = self.client.version()
            return {
                'version': version.get('Version'),
                'api_version': version.get('ApiVersion'),
                'platform': version.get('Platform', {}).get('Name'),
                'os': version.get('Os'),
                'arch': version.get('Arch')
            }
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise
    
    def get_images(self):
        """Get Docker images"""
        try:
            images = self.client.images.list()
            return [{
                'id': img.id[:12],
                'tags': img.tags,
                'size': img.attrs.get('Size'),
                'created': img.attrs.get('Created'),
                'author': img.attrs.get('Author', ''),
                'architecture': img.attrs.get('Architecture', '')
            } for img in images]
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise
    
    def pull_image(self, image_name, tag='latest'):
        """Pull Docker image"""
        try:
            result = self.client.images.pull(image_name, tag=tag)
            return {
                'id': result.id[:12],
                'name': f"{image_name}:{tag}",
                'success': True
            }
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def build_image(self, path, image_name, tag='latest', dockerfile='Dockerfile'):
        """Build Docker image"""
        try:
            # Check if path is a file or directory
            if os.path.isfile(path):
                # Single file - create tar
                with open(path, 'rb') as f:
                    fileobj = io.BytesIO(f.read())
                result = self.client.images.build(
                    fileobj=fileobj,
                    tag=f"{image_name}:{tag}",
                    dockerfile=dockerfile
                )
            else:
                # Directory
                result = self.client.images.build(
                    path=path,
                    tag=f"{image_name}:{tag}",
                    dockerfile=dockerfile
                )
            
            # Get image
            image = next(result)
            return {
                'id': image.id[:12],
                'name': f"{image_name}:{tag}",
                'success': True
            }
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_containers(self, all=False):
        """Get Docker containers"""
        try:
            containers = self.client.containers.list(all=all)
            return [{
                'id': c.id[:12],
                'name': c.name,
                'image': c.image.tags[0] if c.image.tags else c.image.id[:12],
                'status': c.status,
                'state': c.attrs.get('State', {}).get('Status'),
                'created': c.attrs.get('Created'),
                'ports': c.attrs.get('NetworkSettings', {}).get('Ports', {})
            } for c in containers]
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise
    
    def create_container(self, image_name, name=None, ports=None, environment=None, command=None):
        """Create Docker container"""
        try:
            container = self.client.containers.create(
                image=image_name,
                name=name,
                ports=ports,
                environment=environment,
                command=command
            )
            return {
                'id': container.id[:12],
                'name': container.name,
                'status': container.status
            }
        except APIError as e:
            logger.error(f"Docker API error: {e}")
            raise
    
    def start_container(self, container_id):
        """Start Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return {'success': True, 'id': container.id[:12], 'status': container.status}
        except (APIError, NotFound) as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop_container(self, container_id, timeout=10):
        """Stop Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            return {'success': True, 'id': container.id[:12], 'status': container.status}
        except (APIError, NotFound) as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def restart_container(self, container_id, timeout=10):
        """Restart Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            return {'success': True, 'id': container.id[:12], 'status': container.status}
        except (APIError, NotFound) as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_container(self, container_id, force=False):
        """Remove Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            return {'success': True}
        except (APIError, NotFound) as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_container_logs(self, container_id, tail=100):
        """Get container logs"""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8')
        except (APIError, NotFound) as e:
            logger.error(f"Docker API error: {e}")
            return None
    
    def push_image(self, image_name, tag='latest', registry_url=None):
        """Push Docker image to registry"""
        try:
            image = self.client.images.get(f"{image_name}:{tag}")
            
            if registry_url:
                full_name = f"{registry_url}/{image_name}:{tag}"
                image.tag(full_name)
                result = self.client.images.push(full_name)
            else:
                result = self.client.images.push(f"{image_name}:{tag}")
            
            return {'success': True, 'result': result}
        except (APIError, ImageNotFound) as e:
            logger.error(f"Docker API error: {e}")
            return {'success': False, 'error': str(e)}