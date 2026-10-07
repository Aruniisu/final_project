"""NotificationService — Email + Slack for ALL system events"""
import os
import requests
from datetime import datetime
from .email_service import email_service


class NotificationService:
    def send_email_notification(self, to_email, subject, message, user_settings):
        if not user_settings.get('emailNotifications', True):
            return False, 'Email disabled'
        if not email_service.is_configured():
            return False, 'SMTP not configured'
        return email_service.send(to_email, subject, message)

    def send_slack_notification(self, webhook_url, message, user_settings):
        if not user_settings.get('slackNotifications', False):
            return False, 'Slack disabled'
        if not webhook_url:
            return False, 'No webhook'
        try:
            r = requests.post(webhook_url, json={'text': message, 'mrkdwn': True}, timeout=10)
            return (r.status_code == 200), (None if r.status_code == 200 else f'HTTP {r.status_code}')
        except Exception as e:
            return False, str(e)[:150]

    def notify(self, user, subject, message, event_type='info'):
        """Send for EVERY event — no severity filter."""
        if not user:
            return {'sent': False, 'reason': 'No user'}

        settings = user.get('settings', {})
        results = {'email': None, 'slack': None, 'event_type': event_type}

        if settings.get('emailNotifications', True):
            ok, err = self.send_email_notification(
                user.get('email'), subject, message, settings
            )
            results['email'] = {'success': ok, 'error': err}
            print(f"[NOTIFY] {'✅' if ok else '❌'} Email → {user.get('email')}" + (f" ({err})" if err else ""))

        webhook = (user.get('tokens') or {}).get('slack_webhook')
        if settings.get('slackNotifications', False) and webhook:
            ok, err = self.send_slack_notification(
                webhook, f"*{subject}*\n\n{message}", settings
            )
            results['slack'] = {'success': ok, 'error': err}

        results['sent'] = bool(
            (results['email'] and results['email'].get('success')) or
            (results['slack'] and results['slack'].get('success'))
        )
        return results


notification_service = NotificationService()


# ═══════════════════════════════════════════════════════════
# UNIVERSAL HELPER
# ═══════════════════════════════════════════════════════════
def notify_user_event(user_id, subject, message, event_type='info'):
    if not user_id:
        print(f"[NOTIFY] ❌ No user_id")
        return {'sent': False, 'reason': 'No user_id'}

    try:
        from database.managers.user_manager import UserManager
        from database.connection import db_connection

        um = UserManager(db_connection.get_db())
        user = um.find_by_user_id(user_id)
        if not user:
            print(f"[NOTIFY] ❌ User {user_id} not found")
            return {'sent': False, 'reason': 'User not found'}

        print(f"[NOTIFY] 🔔 {event_type.upper()} | {subject}")
        return notification_service.notify(user, subject, message, event_type)

    except Exception as e:
        print(f"[NOTIFY] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {'sent': False, 'error': str(e)}


# ═══════════════════════════════════════════════════════════
# AGENT HELPERS
# ═══════════════════════════════════════════════════════════
def notify_deploy(user_id, repo_url, project_name, result, duration):
    success = result.get('success', False)
    if success:
        url = result.get('live_url') or result.get('url') or 'N/A'
        subject = f"✅ Deployed: {project_name}"
        message = (f"Deployment successful!\n\n"
                   f"📦 Repo: {repo_url}\n🌐 URL: {url}\n⏱️ Duration: {duration}\n\n"
                   f"Dashboard: http://localhost:3000/dashboard")
    else:
        subject = f"❌ Deploy FAILED: {project_name}"
        message = (f"Deployment failed!\n\n"
                   f"📦 Repo: {repo_url}\n❌ Error: {str(result.get('error', 'Unknown'))[:500]}\n"
                   f"⏱️ Duration: {duration}")
    return notify_user_event(user_id, subject, message, event_type='deploy')


def notify_security(user_id, owner, repo, result):
    critical = result.get('critical', 0)
    high = result.get('high', 0)
    medium = result.get('medium', 0)
    score = result.get('score', 0)
    issues = result.get('issues', [])

    if critical > 0:
        emoji, subject = "🚨", f"🚨 CRITICAL vulnerabilities in {repo}"
    elif high > 0:
        emoji, subject = "⚠️", f"⚠️ High-risk issues in {repo}"
    else:
        emoji, subject = "✅", f"✅ Security scan clean: {repo}"

    top = "\n".join([f"• {i.get('message', '')}" for i in issues[:5]]) or "No issues found"
    message = (f"{emoji} Security Scan Report\n\n"
               f"📦 Repo: {owner}/{repo}\n"
               f"🔴 Critical: {critical}\n🟠 High: {high}\n🟡 Medium: {medium}\n"
               f"📊 Score: {score}/100\n\nTop findings:\n{top}\n\n"
               f"View: http://localhost:3000/settings")
    return notify_user_event(user_id, subject, message, event_type='security')


def notify_pipeline(user_id, repo_url, project_name, result, duration):
    success = result.get('success', False)
    if success:
        subject = f"✅ Pipeline PASSED: {project_name}"
        message = (f"CI/CD pipeline passed!\n\n📦 Repo: {repo_url}\n"
                   f"🔧 Fixes: {result.get('auto_fixes_applied', 0)}\n"
                   f"🎯 Attempts: {result.get('fix_attempts', 0)}\n⏱️ {duration}")
    else:
        subject = f"⚠️ Pipeline FAILED: {project_name}"
        message = (f"Pipeline failed!\n\n📦 Repo: {repo_url}\n"
                   f"🔧 Fixes attempted: {result.get('auto_fixes_applied', 0)}\n"
                   f"❌ Error: {str(result.get('error', 'Unknown'))[:500]}\n⏱️ {duration}\n\n"
                   f"Check: http://localhost:3000/pipelines")
    return notify_user_event(user_id, subject, message, event_type='pipeline')


def notify_code_fix(user_id, result, duration):
    success = result.get('success', False)
    if success:
        pr_url = result.get('pr_url') or result.get('result', {}).get('pr_url')
        if pr_url:
            subject = "🔧 Code fix PR created"
            message = f"Pull request created!\n\n🔗 PR: {pr_url}\n⏱️ {duration}"
        else:
            subject = "🔧 Code fixed"
            message = f"CodeFixerAgent completed\n\n⏱️ {duration}"
    else:
        subject = "❌ Code fix failed"
        message = f"CodeFixerAgent failed\n\n❌ {str(result.get('error', 'Unknown'))[:500]}"
    return notify_user_event(user_id, subject, message, event_type='fix_code')


def notify_monitor(user_id, url, result):
    healthy = result.get('healthy', True)
    if healthy:
        subject = f"✅ Monitor OK: {url}"
        message = f"Your app is UP\n\n🌐 {url}"
    else:
        subject = f"⚠️ Monitor DOWN: {url}"
        message = f"Your app is DOWN!\n\n🌐 {url}\n❌ {result.get('error', 'Unknown')}"
    return notify_user_event(user_id, subject, message, event_type='monitor')


def notify_scale(user_id, service, result):
    old = result.get('old_replicas', result.get('old', 1))
    new = result.get('new_replicas', result.get('replicas', result.get('new', 1)))
    subject = f"📈 Scaled: {service} ({old} → {new})"
    message = f"Scaling complete!\n\n🎯 Service: {service}\n📊 Replicas: {old} → {new}"
    return notify_user_event(user_id, subject, message, event_type='scale')


def notify_agent_action(user_id, agent_name, action, success, result, duration):
    emoji = "✅" if success else "❌"
    subject = f"{emoji} {agent_name}: {action}"
    message = (f"Agent: {agent_name}\nAction: {action}\n"
               f"Status: {'Success' if success else 'Failed'}\nDuration: {duration}")
    if isinstance(result, dict):
        if result.get('error'):
            message += f"\n\nError: {str(result['error'])[:300]}"
        elif result.get('response'):
            message += f"\n\n{str(result['response'])[:500]}"
    return notify_user_event(user_id, subject, message, event_type='agent')


def notify_disk_alert(user_id, usage, free_gb, total_gb):
    subject = f"💾 Disk {usage}% on server"
    message = f"Disk critical!\n\n💾 {usage}%\n📊 Total: {total_gb} GB\n🆓 Free: {free_gb} GB"
    return notify_user_event(user_id, subject, message, event_type='infra')


def notify_memory_alert(user_id, usage):
    subject = f"🧠 Memory {usage}% on server"
    message = f"Memory critical!\n\n🧠 {usage}% used"
    return notify_user_event(user_id, subject, message, event_type='infra')