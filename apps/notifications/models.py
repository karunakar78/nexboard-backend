from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Notification(TimeStampedModel):

    class Type(models.TextChoices):
        TASK_ASSIGNED  = 'task_assigned',   'Task Assigned'
        TASK_COMMENTED = 'task_commented',  'Task Commented'
        TASK_STATUS    = 'task_status',     'Task Status Changed'
        WORKSPACE_INVITE = 'workspace_invite', 'Workspace Invite'

    recipient  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type       = models.CharField(max_length=30, choices=Type.choices)
    title      = models.CharField(max_length=255)
    body       = models.TextField(blank=True)
    is_read    = models.BooleanField(default=False)
    # Generic link back to whatever triggered this notification
    action_url = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient.email} — {self.title}'