import smtplib
import os
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL', '')
    
    def send_email(self, to, subject, body, html_body=None, attachments=None):
        """Send email notification"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to
            msg['Subject'] = subject
            
            # Body
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Attachments
            if attachments:
                for attachment in attachments:
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    def send_slack(self, message, channel=None, attachments=None):
        """Send Slack notification"""
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return False
        
        try:
            payload = {
                'text': message,
                'channel': channel
            }
            
            if attachments:
                payload['attachments'] = attachments
            
            response = requests.post(
                self.slack_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code == 200
            if success:
                logger.info("Slack notification sent")
            else:
                logger.error(f"Slack error: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Slack send error: {e}")
            return False
    
    def send_teams(self, message, title=None, color=None):
        """Send Microsoft Teams notification"""
        if not self.teams_webhook:
            logger.warning("Teams webhook not configured")
            return False
        
        try:
            payload = {
                'text': f"**{title or 'Notification'}**\n\n{message}" if title else message
            }
            
            if color:
                payload['themeColor'] = color
            
            response = requests.post(
                self.teams_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code == 200
            if success:
                logger.info("Teams notification sent")
            else:
                logger.error(f"Teams error: {response.status_code}")
            
            return success
        except Exception as e:
            logger.error(f"Teams send error: {e}")
            return False
    
    def send_deployment_notification(self, deployment, status):
        """Send deployment status notification"""
        subject = f"Deployment {status}: {deployment.get('name', 'Unknown')}"
        body = f"""
Deployment Status: {status}
Name: {deployment.get('name', 'Unknown')}
Environment: {deployment.get('environment', 'Unknown')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Logs: {deployment.get('logs', [])}
        """
        
        # Send email
        if deployment.get('user_email'):
            self.send_email(
                to=deployment['user_email'],
                subject=subject,
                body=body
            )
        
        # Send Slack
        self.send_slack(
            f"🚀 *{status}*: {deployment.get('name', 'Unknown')} deployed to {deployment.get('environment', 'Unknown')}",
            channel=deployment.get('slack_channel')
        )
    
    def send_pipeline_notification(self, pipeline, status):
        """Send pipeline status notification"""
        subject = f"Pipeline {status}: {pipeline.get('name', 'Unknown')}"
        body = f"""
Pipeline Status: {status}
Name: {pipeline.get('name', 'Unknown')}
Branch: {pipeline.get('branch', 'Unknown')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Steps: {pipeline.get('steps', [])}
        """
        
        if pipeline.get('user_email'):
            self.send_email(
                to=pipeline['user_email'],
                subject=subject,
                body=body
            )
        
        self.send_slack(
            f"🔄 *{status}*: {pipeline.get('name', 'Unknown')} pipeline",
            channel=pipeline.get('slack_channel')
        )
    
    def send_alert_notification(self, alert):
        """Send alert notification"""
        subject = f"Alert: {alert.get('severity', 'unknown')} - {alert.get('title', '')}"
        body = f"""
Alert: {alert.get('title', '')}
Severity: {alert.get('severity', 'unknown')}
Message: {alert.get('message', '')}
Source: {alert.get('source', 'Unknown')}
Time: {alert.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
        """
        
        # Critical alerts get all channels
        if alert.get('severity') in ['critical', 'high']:
            if alert.get('user_email'):
                self.send_email(
                    to=alert['user_email'],
                    subject=f"🚨 {subject}",
                    body=body
                )
            
            self.send_slack(
                f"🚨 *{alert.get('severity').upper()}*: {alert.get('title', '')}\n{alert.get('message', '')}",
                channel=alert.get('slack_channel')
            )
        else:
            self.send_slack(
                f"⚠️ *{alert.get('severity').upper()}*: {alert.get('title', '')}",
                channel=alert.get('slack_channel')
            )