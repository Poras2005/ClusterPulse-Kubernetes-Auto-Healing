import logging, time, json
from datetime import datetime, timezone

log = logging.getLogger('clusterpulse.healer.memory_leak')

class MemoryLeakHealer:
    def __init__(self, prom_client, k8s_client, notifier, cfg):
        self.prom = prom_client
        self.k8s = k8s_client
        self.notifier = notifier
        self.cfg = cfg['healers']['memory_leak']
        self.cooldown = {} # pod_name -> last_heal_time

    def run(self, namespace):
        """Check all pods in namespace for memory leaks using percentages."""
        if not self.cfg['enabled']:
            return
            
        threshold_percent = self.cfg['threshold_percent']
        window_min = self.cfg['trend_window_minutes']
        slope_percent = self.cfg['slope_threshold_percent_per_min']
        
        pod_metrics = self.prom.bulk_pod_memory_trend(namespace, window_min)
        
        for pod_name, metrics in pod_metrics.items():
            if self._in_cooldown(pod_name):
                continue
                
            current_pct = metrics['current_percent']
            slope = metrics['slope_percent_per_min']
            limit_mb = metrics['limit_mb']
            current_mb = metrics['current_mb']
            
            if current_pct >= threshold_percent and slope >= slope_percent:
                reason = (f'Memory at {current_pct:.1f}% ({current_mb:.0f}MB/{limit_mb:.0f}MB), '
                          f'growing at {slope:.1f}%/min (threshold: {slope_percent}%/min)')
                log.warning(f'LEAK DETECTED — {pod_name}: {reason}')
                self._heal(namespace, pod_name, reason)

    def _heal(self, namespace, pod_name, reason):
        deploy_name = self.k8s.get_deployment_for_pod(namespace, pod_name)
        if not deploy_name:
            log.error(f"Could not resolve Deployment for pod {pod_name}. Skipping restart.")
            return

        self.k8s.rolling_restart(namespace, deploy_name)
        
        audit_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "healer": "memory_leak",
            "namespace": namespace,
            "target": pod_name,
            "action": "rolling_restart",
            "reason": reason
        }
        log.info(f"AUDIT_EVENT: {json.dumps(audit_event)}")
            
        self.notifier.send(
            healer='memory_leak', target=pod_name,
            action='rolling_restart', reason=reason, namespace=namespace)
            
        self.cooldown[pod_name] = datetime.now(timezone.utc)
        log.info(f'Healing complete for {pod_name}')

    def _in_cooldown(self, pod_name):
        if pod_name not in self.cooldown:
            return False
        elapsed = (datetime.now(timezone.utc) - self.cooldown[pod_name]).total_seconds() / 60
        return elapsed < self.cfg['cooldown_minutes']
