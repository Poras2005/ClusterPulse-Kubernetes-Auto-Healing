import requests, boto3, logging

log = logging.getLogger('kubeguard.notifier')

class Notifier:
    def __init__(self, slack_webhook='', sns_topic_arn='', aws_creds=None):
        self.slack_webhook = slack_webhook
        self.sns_topic_arn = sns_topic_arn
        self.aws_creds = aws_creds or {}

    def send(self, healer, target, action, reason):
        emoji = {'memory_leak': '🧠'}.get(healer, '🔧')
        msg = (f'{emoji} *KubeGuard Auto-Heal*\n'
               f'*Healer:* {healer}\n'
               f'*Target:* {target}\n'
               f'*Action:* {action}\n'
               f'*Reason:* {reason}')
        self._slack(msg)
        self._sns(msg)

    def _slack(self, msg):
        if not self.slack_webhook:
            return
        try:
            requests.post(self.slack_webhook, json={'text': msg}, timeout=5)
            log.info('Slack notification sent')
        except Exception as e:
            log.warning(f'Slack failed (non-fatal): {e}')

    def _sns(self, msg):
        if not self.sns_topic_arn or not self.aws_creds:
            return
        try:
            sns = boto3.client('sns',
                region_name=self.aws_creds.get('region_name', 'ap-south-1'),
                aws_access_key_id=self.aws_creds.get('aws_access_key_id'),
                aws_secret_access_key=self.aws_creds.get('aws_secret_access_key'))
            sns.publish(TopicArn=self.sns_topic_arn, Message=msg,
                        Subject='KubeGuard Alert')
            log.info('SNS notification sent')
        except Exception as e:
            log.warning(f'SNS failed (non-fatal): {e}')
