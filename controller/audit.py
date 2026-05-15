import boto3, uuid, logging
from datetime import datetime, timezone

log = logging.getLogger('kubeguard.audit')

class AuditLogger:
    def __init__(self, creds, table_name, region):
        self.table = boto3.resource('dynamodb',
            region_name=region,
            aws_access_key_id=creds.get('aws_access_key_id'),
            aws_secret_access_key=creds.get('aws_secret_access_key')
        ).Table(table_name)

    def log_event(self, healer, namespace, target, action, reason, details=''):
        """Write a healing event to DynamoDB."""
        item = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healer': healer,
            'namespace': namespace,
            'target': target,
            'action': action,
            'reason': reason,
            'details': details,
        }
        try:
            self.table.put_item(Item=item)
            log.info(f'Audit logged: {action} on {target}')
        except Exception as e:
            log.error(f'Audit log failed: {e}')
        return item
