import logging, time
from datetime import datetime, timezone

log = logging.getLogger('kubeguard.healer.memory_leak')

class MemoryLeakHealer:
    def __init__(self, prom_client, k8s_client, audit, notifier, cfg):
        self.prom = prom_client
        self.k8s = k8s_client
        self.audit = audit
        self.notifier = notifier
        self.cfg = cfg['healers']['memory_leak']
        self.cooldown = {} # pod_name -> last_heal_time

    def run(self, namespace):
        """Check all pods in namespace for memory leaks."""
        if not self.cfg['enabled']:
            return
            
        pods = self.k8s.list_pods(namespace)
        for pod in pods:
            pod_name = pod.metadata.name
            # Skip if in cooldown
            if self._in_cooldown(pod_name):
                continue
            self._check_pod(namespace, pod_name)

    def _check_pod(self, namespace, pod_name):
        threshold_mb = self.cfg['threshold_mb']
        window_min = self.cfg['trend_window_minutes']
        slope_thresh = self.cfg['slope_threshold_mb_per_min']
        
        current_mb = self.prom.pod_memory_mb(namespace, pod_name)
        if current_mb < threshold_mb:
            return # below watch threshold, skip
            
        slope = self.prom.pod_memory_trend_mb_per_min(namespace, pod_name, window_min)
        log.info(f'{pod_name}: {current_mb:.0f}MB, slope={slope:.1f}MB/min')
        
        if slope >= slope_thresh:
            reason = (f'Memory {current_mb:.0f}MB, growing at {slope:.1f}MB/min '
                      f'(threshold: {slope_thresh}MB/min)')
            log.warning(f'LEAK DETECTED — {pod_name}: {reason}')
            self._heal(namespace, pod_name, reason)

    def _heal(self, namespace, pod_name, reason):
        # Find the deployment owning this pod
        deploy_name = pod_name.rsplit('-', 2)[0] # strip hash suffixes
        self.k8s.rolling_restart(namespace, deploy_name)
        
        self.audit.log_event(
            healer='memory_leak', namespace=namespace,
            target=pod_name, action='rolling_restart', reason=reason)
            
        self.notifier.send(
            healer='memory_leak', target=pod_name,
            action='rolling_restart', reason=reason)
            
        self.cooldown[pod_name] = datetime.now(timezone.utc)
        log.info(f'Healing complete for {pod_name}')

    def _in_cooldown(self, pod_name):
        if pod_name not in self.cooldown:
            return False
        elapsed = (datetime.now(timezone.utc) - self.cooldown[pod_name]).total_seconds() / 60
        return elapsed < self.cfg['cooldown_minutes']
