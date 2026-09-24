import requests, logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger('clusterpulse.prometheus')

class PrometheusClient:
    def __init__(self, url='http://prometheus-server.monitoring.svc:9090'):
        self.url = url

    def query(self, promql):
        """Run an instant PromQL query. Returns list of results."""
        try:
            r = requests.get(f'{self.url}/api/v1/query',
                             params={'query': promql}, timeout=10)
            r.raise_for_status()
            return r.json()['data']['result']
        except Exception as e:
            log.error(f'Prometheus instant query failed: {e}')
            return []

    def query_range(self, promql, minutes=5):
        """Run a range query over the last N minutes."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=minutes)
        try:
            r = requests.get(f'{self.url}/api/v1/query_range', params={
                'query': promql,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': '30s'
            }, timeout=10)
            r.raise_for_status()
            return r.json()['data']['result']
        except Exception as e:
            log.error(f'Prometheus range query failed: {e}')
            return []

    def bulk_pod_memory_trend(self, namespace, window_minutes=5):
        """Calculate memory growth rate (%) and current usage (%) relative to limits for all pods in namespace."""
        
        # 1. Fetch memory limits for all pods
        q_limits = f'kube_pod_container_resource_limits{{namespace="{namespace}",resource="memory"}}'
        limit_results = self.query(q_limits)
        limits = {}
        for res in limit_results:
            pod = res.get('metric', {}).get('pod')
            if pod:
                # Sum limits if there are multiple containers in a pod
                limits[pod] = limits.get(pod, 0.0) + float(res['value'][1])

        # 2. Fetch memory usage over time
        q_mem = f'sum by (pod) (container_memory_working_set_bytes{{namespace="{namespace}",container!="POD",pod!=""}})'
        results = self.query_range(q_mem, minutes=window_minutes)
        
        trends = {}
        if not results:
            return trends
            
        for res in results:
            metric = res.get('metric', {})
            pod = metric.get('pod')
            
            # Skip if we don't have a limit for this pod
            if not pod or pod not in limits or limits[pod] == 0:
                continue
                
            limit_bytes = limits[pod]

            values = [(float(ts), float(v)) for ts, v in res.get('values', [])]
            if len(values) < 2:
                continue
                
            elapsed_min = (values[-1][0] - values[0][0]) / 60
            if elapsed_min == 0:
                continue
                
            delta_bytes = values[-1][1] - values[0][1]
            slope_bytes_per_min = delta_bytes / elapsed_min
            current_bytes = values[-1][1]
            
            trends[pod] = {
                'current_percent': (current_bytes / limit_bytes) * 100,
                'slope_percent_per_min': (slope_bytes_per_min / limit_bytes) * 100,
                'limit_mb': limit_bytes / 1024 / 1024,
                'current_mb': current_bytes / 1024 / 1024
            }
            
        return trends
