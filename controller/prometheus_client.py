import requests, logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger('kubeguard.prometheus')

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
            log.error(f'Prometheus query failed: {e}')
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

    def pod_memory_mb(self, namespace, pod_name):
        """Current memory usage of a pod in MB."""
        q = (f'container_memory_working_set_bytes{{namespace="{namespace}",'
             f'pod=~"{pod_name}.*",container!="POD"}}')
        res = self.query(q)
        if res:
            return float(res[0]['value'][1]) / 1024 / 1024
        return 0.0

    def pod_memory_trend_mb_per_min(self, namespace, pod_name, window_minutes=5):
        """Calculate memory growth rate (MB/min) over the window.
        Positive slope = growing = potential leak.
        """
        q = (f'container_memory_working_set_bytes{{namespace="{namespace}",'
             f'pod=~"{pod_name}.*",container!="POD"}}')
        results = self.query_range(q, minutes=window_minutes)
        if not results or not results[0]['values']:
            return 0.0
            
        values = [(float(ts), float(v)) for ts, v in results[0]['values']]
        if len(values) < 2:
            return 0.0
            
        # Simple linear slope: (last - first) / elapsed_minutes
        elapsed_min = (values[-1][0] - values[0][0]) / 60
        if elapsed_min == 0:
            return 0.0
        delta_mb = (values[-1][1] - values[0][1]) / 1024 / 1024
        return delta_mb / elapsed_min

    def get_request_rate_slope(self, namespace, deployment_name, window_minutes=5):
        """Calculate slope of request rate. 
        High memory slope + Flat/Low request slope = Confirmed Leak.
        """
        q = (f'rate(http_requests_total{{namespace="{namespace}",'
             f'deployment="{deployment_name}"}}[{window_minutes}m])')
        results = self.query_range(q, minutes=window_minutes)
        if not results or not results[0]['values']:
            return 0.0
        values = [(float(ts), float(v)) for ts, v in results[0]['values']]
        if len(values) < 2: return 0.0
        return (values[-1][1] - values[0][1]) / ((values[-1][0] - values[0][0]) / 60)
