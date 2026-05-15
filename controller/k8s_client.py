from kubernetes import client, config as k8s_config
import logging
from datetime import datetime, timezone

log = logging.getLogger('kubeguard.k8s')

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
        'kubeguard/restartedAt': datetime.now(timezone.utc).isoformat()
    }}}}}
    apps.patch_namespaced_deployment(deployment_name, namespace, patch)
    log.info(f'Rolling restart triggered: {namespace}/{deployment_name}')

def list_pods(namespace, label_selector=None):
    """List pods, optionally filtered by label selector."""
    core = client.CoreV1Api()
    return core.list_namespaced_pod(
        namespace, label_selector=label_selector).items

def get_deployment_replicas(namespace, deployment_name):
    """Get current replica count for a deployment."""
    apps = client.AppsV1Api()
    d = apps.read_namespaced_deployment(deployment_name, namespace)
    return d.spec.replicas
