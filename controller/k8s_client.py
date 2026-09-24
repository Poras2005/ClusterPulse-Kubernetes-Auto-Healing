from kubernetes import client, config as k8s_config
import logging
from datetime import datetime, timezone

log = logging.getLogger('clusterpulse.k8s')

def load_k8s_config():
    """Load in-cluster config (when running inside K8s)
    or local kubeconfig (for local dev with Minikube).
    """
    try:
        k8s_config.load_incluster_config() # running inside K8s pod
        log.info('Loaded in-cluster Kubernetes config')
    except k8s_config.ConfigException:
        k8s_config.load_kube_config() # local dev / minikube
        log.info('Loaded local kubeconfig')

def rolling_restart(namespace, deployment_name):
    """Trigger a rolling restart of a deployment.
    Equivalent to: kubectl rollout restart deployment/<name>
    """
    apps = client.AppsV1Api()
    patch = {'spec': {'template': {'metadata': {'annotations': {
        'clusterpulse/restartedAt': datetime.now(timezone.utc).isoformat()
    }}}}}
    apps.patch_namespaced_deployment(deployment_name, namespace, patch)
    log.info(f'Rolling restart triggered: {namespace}/{deployment_name}')

def get_deployment_for_pod(namespace, pod_name):
    """Resolve Pod -> ReplicaSet -> Deployment using owner references."""
    core = client.CoreV1Api()
    apps = client.AppsV1Api()
    
    try:
        pod = core.read_namespaced_pod(pod_name, namespace)
        if not pod.metadata.owner_references:
            return None
            
        rs_ref = next((ref for ref in pod.metadata.owner_references if ref.kind == 'ReplicaSet'), None)
        if not rs_ref:
            return None
            
        rs = apps.read_namespaced_replica_set(rs_ref.name, namespace)
        if not rs.metadata.owner_references:
            return None
            
        deploy_ref = next((ref for ref in rs.metadata.owner_references if ref.kind == 'Deployment'), None)
        if not deploy_ref:
            return None
            
        return deploy_ref.name
    except Exception as e:
        log.error(f"Error resolving deployment for pod {pod_name}: {e}")
        return None
