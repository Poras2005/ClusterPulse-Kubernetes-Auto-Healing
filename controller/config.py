import yaml
from pathlib import Path

def load_config():
    path = Path(__file__).parent.parent / 'config.yaml'
    if not path.exists():
        # Default config if file is missing (for safety)
        return {
            'kubernetes': {'namespace': 'default', 'watch_interval_seconds': 15},
            'healers': {
                'memory_leak': {
                    'enabled': True, 
                    'threshold_percent': 80, 
                    'trend_window_minutes': 5, 
                    'slope_threshold_percent_per_min': 5, 
                    'cooldown_minutes': 10
                }
            }
        }
    with open(path) as f:
        return yaml.safe_load(f)
