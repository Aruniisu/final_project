"""EmailService — Real SMTP email sending via Gmail"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailService:
    def __init__(self):
        self.host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('SMTP_PORT', 587))
        self.user = os.getenv('SMTP_USER')
        self.password = os.getenv('SMTP_PASSWORD')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Smart DevOps')

    def is_configured(self):
        return bool(self.user and self.password)

    def send(self, to_email, subject, body, html_body=None):
        """Send email. Returns (success, error)."""
        if not self.is_configured():
            return False, 'SMTP not configured'

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.user}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            if not html_body:
                html_body = self._build_html(subject, body)
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.host, self.port, timeout=15)
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
            server.quit()

            print(f"[EMAIL] ✅ Sent to {to_email}: {subject}")
            return True, None

        except smtplib.SMTPAuthenticationError:
            return False, 'SMTP auth failed — check app password'
        except smtplib.SMTPException as e:
            return False, f'SMTP error: {str(e)[:200]}'
        except Exception as e:
            return False, f'Email error: {str(e)[:200]}'

    def _build_html(self, subject, body):
        safe_body = body.replace('\n', '<br>')
        return f"""
        <html>
        <body style="font-family: -apple-system, sans-serif; background: #0f172a; padding: 40px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 32px; border: 1px solid #334155;">
            <div style="text-align: center; margin-bottom: 24px;">
              <div style="display: inline-block; padding: 12px 16px; background: linear-gradient(135deg, #a855f7, #6366f1); border-radius: 12px; font-size: 24px;">🤖</div>
              <h1 style="color: #fff; margin: 16px 0 4px; font-size: 20px;">Smart DevOps</h1>
              <p style="color: #94a3b8; margin: 0; font-size: 13px;">{subject}</p>
            </div>
            <div style="color: #e2e8f0; font-size: 14px; line-height: 1.6;">
              {safe_body}
            </div>
            <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #334155; text-align: center; color: #64748b; font-size: 11px;">
              Sent by Smart DevOps Assistant · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
          </div>
        </body>
        </html>
        """


email_service = EmailService()