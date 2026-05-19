from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_assigned_email(self, assignee_email, task_title, project_name, assigner_name):
    """
    bind=True         — gives access to `self` (the task instance) for retries
    max_retries=3     — retry up to 3 times on failure
    default_retry_delay=60 — wait 60 seconds between retries
    """
    try:
        send_mail(
            subject=f'[NexBoard] You were assigned: {task_title}',
            message=(
                f'Hi,\n\n'
                f'{assigner_name} assigned you to "{task_title}" '
                f'in the {project_name} project.\n\n'
                f'Log in to NexBoard to view the task.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assignee_email],
            fail_silently=False,
        )
    except Exception as exc:
        # Retry the task — Celery will wait 60s and try again
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_comment_notification_email(self, recipient_email, commenter_name, task_title):
    try:
        send_mail(
            subject=f'[NexBoard] New comment on: {task_title}',
            message=(
                f'Hi,\n\n'
                f'{commenter_name} commented on "{task_title}".\n\n'
                f'Log in to NexBoard to view the comment.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_workspace_invite_email(self, recipient_email, inviter_name, workspace_name, invite_token):
    try:
        send_mail(
            subject=f'[NexBoard] You\'re invited to {workspace_name}',
            message=(
                f'Hi,\n\n'
                f'{inviter_name} invited you to join the "{workspace_name}" workspace '
                f'on NexBoard.\n\n'
                f'Use this token to accept: {invite_token}\n\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def create_in_app_notification(recipient_id, notif_type, title, body='', action_url=''):
    """
    Creates a Notification record in the DB.
    Kept separate from email tasks so each can fail/retry independently.
    """
    from apps.notifications.models import Notification
    Notification.objects.create(
        recipient_id=recipient_id,
        type=notif_type,
        title=title,
        body=body,
        action_url=action_url,
    )