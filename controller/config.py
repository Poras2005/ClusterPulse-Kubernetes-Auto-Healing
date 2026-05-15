import os, yaml, getpass
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
                    'threshold_mb': 800, 
                    'trend_window_minutes': 5, 
                    'slope_threshold_mb_per_min': 20, 
                    'cooldown_minutes': 10
                }
            },
            'audit': {'dynamodb_table': 'kubeguard-events', 'aws_region': 'ap-south-1'}
        }
    with open(path) as f:
        return yaml.safe_load(f)

def get_aws_creds():
    """Reads AWS creds from env vars (for EKS/CI) or prompts
    at runtime (for local dev). Never stored in any file.
    """
    key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_REGION', 'ap-south-1')
    
    if not key_id:
        print(' KubeGuard — AWS credentials for DynamoDB + SNS')
        key_id = getpass.getpass(' AWS Access Key ID : ')
        secret = getpass.getpass(' AWS Secret Access Key : ')
        
    return {
        'aws_access_key_id': key_id,
        'aws_secret_access_key': secret,
        'region_name': region
    }
