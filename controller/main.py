#!/usr/bin/env python3
"""
KubeGuard Controller — runs healers in a continuous loop.
Usage: python3 controller/main.py
"""
import logging, time, threading, sys, os, signal
from config import load_config, get_aws_creds
from k8s_client import load_k8s_config, rolling_restart, list_pods, get_deployment_replicas
from prometheus_client import PrometheusClient
from audit import AuditLogger
from notifier import Notifier
from healers.memory_leak import MemoryLeakHealer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('kubeguard.main')

# Simple namespace object to pass k8s functions as group
class K8sClient:
    rolling_restart = staticmethod(rolling_restart)
    list_pods = staticmethod(list_pods)
    get_deployment_replicas = staticmethod(get_deployment_replicas)

def run_healer(healer, namespace, interval):
    """Run a healer in a loop every interval seconds."""
    name = healer.__class__.__name__
    log.info(f'Starting {name}')
    while True:
        try:
            healer.run(namespace)
        except Exception as e:
            log.error(f'{name} error: {e}')
        time.sleep(interval)

def main():
    cfg = load_config()
    creds = get_aws_creds()
    ns = cfg['kubernetes']['namespace']
    interval = cfg['kubernetes']['watch_interval_seconds']
    
    # Load Kubernetes config (in-cluster or local kubeconfig)
    load_k8s_config()
    
    # Shared clients
    prom_url = os.environ.get('PROMETHEUS_URL') or cfg['kubernetes'].get('prometheus_url', 'http://prometheus-server.monitoring.svc:9090')
    prom = PrometheusClient(url=prom_url)
    k8s = K8sClient()
    audit = AuditLogger(creds, cfg['audit']['dynamodb_table'], 
                        cfg['audit']['aws_region'])
    
    slack_webhook = os.environ.get('SLACK_WEBHOOK') or cfg.get('alerts', {}).get('slack_webhook')
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN') or cfg.get('alerts', {}).get('sns_topic_arn')
    
    notify = Notifier(
        slack_webhook=slack_webhook,
        sns_topic_arn=sns_topic_arn,
        aws_creds=creds)
    
    # Build healers
    healers = [
        MemoryLeakHealer(prom, k8s, audit, notify, cfg),
    ]
    
    log.info('KubeGuard controller started — watching namespace: %s', ns)
    
    def signal_handler(sig, frame):
        log.info('Graceful shutdown initiated...')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    threads = [threading.Thread(target=run_healer, 
                                args=(h, ns, interval), daemon=True) for h in healers]
    for t in threads:
        t.start()
        
    # Keep main thread alive
    try:
        while True: time.sleep(60)
    except KeyboardInterrupt:
        log.info('KubeGuard stopped by user')
        sys.exit(0)

if __name__ == '__main__':
    main()
