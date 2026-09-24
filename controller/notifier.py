import logging
from kubernetes import client
from datetime import datetime, timezone

log = logging.getLogger('clusterpulse.notifier')

class Notifier:
    def __init__(self):
        self.core_v1 = client.CoreV1Api()

    def send(self, healer, target, action, reason, namespace='default'):
        msg = f"clusterpulse Auto-Heal | Healer: {healer} | Action: {action} | Reason: {reason}"
        event = client.CoreV1Event(
            metadata=client.V1ObjectMeta(
                generate_name=f"clusterpulse-{healer}-",
                namespace=namespace
            ),
            type="Warning",
            reason="MemoryLeakDetected" if healer == 'memory_leak' else "AutoHealTriggered",
            message=msg,
            source=client.V1EventSource(component="clusterpulse-controller"),
            involved_object=client.V1ObjectReference(
                kind="Pod",
                name=target,
                namespace=namespace
            ),
            first_timestamp=datetime.now(timezone.utc),
            last_timestamp=datetime.now(timezone.utc),
            count=1
        )
        try:
            self.core_v1.create_namespaced_event(namespace, event)
            log.info(f"Kubernetes event emitted for {target}")
        except Exception as e:
            log.error(f"Failed to emit Kubernetes event: {e}")
