import os
import yaml
import json
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class KubernetesService:
    """Service for interacting with Kubernetes API"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or os.getenv('KUBE_CONFIG_PATH', '~/.kube/config')
        self._load_config()
    
    def _load_config(self):
        """Load Kubernetes configuration"""
        try:
            config.load_kube_config(config_file=os.path.expanduser(self.config_path))
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.authenticated = True
        except Exception as e:
            logger.error(f"Kubernetes config error: {e}")
            self.authenticated = False
    
    def is_authenticated(self):
        """Check if authenticated with Kubernetes"""
        return self.authenticated
    
    def get_cluster_info(self):
        """Get cluster information"""
        try:
            version = client.VersionApi().get_code()
            return {
                'version': version.git_version,
                'platform': version.platform,
                'build_date': version.build_date,
                'go_version': version.go_version
            }
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_nodes(self):
        """Get cluster nodes"""
        try:
            nodes = self.core_v1.list_node()
            return [{
                'name': node.metadata.name,
                'status': node.status.conditions[-1].type if node.status.conditions else 'Unknown',
                'roles': self._get_node_roles(node),
                'age': self._get_age(node.metadata.creation_timestamp),
                'version': node.status.node_info.kubelet_version,
                'os': node.status.node_info.operating_system,
                'architecture': node.status.node_info.architecture,
                'capacity': node.status.capacity,
                'allocatable': node.status.allocatable
            } for node in nodes.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_namespaces(self):
        """Get namespaces"""
        try:
            namespaces = self.core_v1.list_namespace()
            return [{
                'name': ns.metadata.name,
                'status': ns.status.phase,
                'created_at': ns.metadata.creation_timestamp.isoformat()
            } for ns in namespaces.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_pods(self, namespace='default'):
        """Get pods in namespace"""
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            return [{
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'created_at': pod.metadata.creation_timestamp.isoformat(),
                'containers': [{'name': c.name, 'image': c.image, 'ready': c.ready} for c in pod.status.container_statuses] if pod.status.container_statuses else []
            } for pod in pods.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_deployments(self, namespace='default'):
        """Get deployments in namespace"""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            return [{
                'name': dep.metadata.name,
                'namespace': dep.metadata.namespace,
                'replicas': dep.spec.replicas,
                'ready_replicas': dep.status.ready_replicas or 0,
                'available_replicas': dep.status.available_replicas or 0,
                'updated_replicas': dep.status.updated_replicas or 0,
                'created_at': dep.metadata.creation_timestamp.isoformat()
            } for dep in deployments.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_services(self, namespace='default'):
        """Get services in namespace"""
        try:
            services = self.core_v1.list_namespaced_service(namespace=namespace)
            return [{
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'type': svc.spec.type,
                'cluster_ip': svc.spec.cluster_ip,
                'ports': [{'port': p.port, 'target_port': p.target_port, 'protocol': p.protocol} for p in svc.spec.ports] if svc.spec.ports else []
            } for svc in services.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def get_ingress(self, namespace='default'):
        """Get ingress in namespace"""
        try:
            ingresses = self.networking_v1.list_namespaced_ingress(namespace=namespace)
            return [{
                'name': ing.metadata.name,
                'namespace': ing.metadata.namespace,
                'hosts': [rule.host for rule in ing.spec.rules] if ing.spec.rules else []
            } for ing in ingresses.items]
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def apply_yaml(self, yaml_content, namespace='default'):
        """Apply Kubernetes YAML"""
        try:
            # Parse YAML
            resources = list(yaml.safe_load_all(yaml_content))
            results = []
            
            for resource in resources:
                kind = resource.get('kind')
                name = resource.get('metadata', {}).get('name')
                resource['metadata']['namespace'] = namespace
                
                if kind == 'Deployment':
                    result = self.apps_v1.create_namespaced_deployment(namespace=namespace, body=resource)
                elif kind == 'Service':
                    result = self.core_v1.create_namespaced_service(namespace=namespace, body=resource)
                elif kind == 'Ingress':
                    result = self.networking_v1.create_namespaced_ingress(namespace=namespace, body=resource)
                elif kind == 'ConfigMap':
                    result = self.core_v1.create_namespaced_config_map(namespace=namespace, body=resource)
                elif kind == 'Secret':
                    result = self.core_v1.create_namespaced_secret(namespace=namespace, body=resource)
                else:
                    results.append({
                        'kind': kind,
                        'name': name,
                        'status': 'skipped',
                        'message': f'Unsupported kind: {kind}'
                    })
                    continue
                
                results.append({
                    'kind': kind,
                    'name': name,
                    'status': 'created',
                    'namespace': namespace
                })
            
            return results
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e.body if hasattr(e, 'body') else str(e)}")
            raise
    
    def delete_resource(self, kind, name, namespace='default'):
        """Delete Kubernetes resource"""
        try:
            if kind == 'Deployment':
                result = self.apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
            elif kind == 'Service':
                result = self.core_v1.delete_namespaced_service(name=name, namespace=namespace)
            elif kind == 'Ingress':
                result = self.networking_v1.delete_namespaced_ingress(name=name, namespace=namespace)
            elif kind == 'Pod':
                result = self.core_v1.delete_namespaced_pod(name=name, namespace=namespace)
            else:
                return {'success': False, 'message': f'Unsupported kind: {kind}'}
            
            return {'success': True, 'kind': kind, 'name': name, 'namespace': namespace}
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def scale_deployment(self, name, replicas, namespace='default'):
        """Scale a deployment"""
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            deployment.spec.replicas = replicas
            
            # Update deployment
            result = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                'success': True,
                'name': name,
                'namespace': namespace,
                'replicas': replicas
            }
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_node_roles(self, node):
        """Get node roles from labels"""
        labels = node.metadata.labels or {}
        roles = []
        for label, value in labels.items():
            if 'node-role.kubernetes.io/' in label:
                role = label.split('/')[-1]
                if role not in roles:
                    roles.append(role)
        return roles if roles else ['<none>']
    
    def _get_age(self, timestamp):
        """Calculate age from timestamp"""
        from datetime import datetime
        age = datetime.now() - timestamp
        days = age.days
        hours = age.seconds // 3600
        minutes = (age.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"