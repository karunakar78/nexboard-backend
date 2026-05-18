from django.conf import settings
from django.db import models

from common.models import TimeStampedModel
from apps.workspaces.models import Workspace


class Project(TimeStampedModel):

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        ARCHIVED  = 'archived',  'Archived'
        COMPLETED = 'completed', 'Completed'

    class Visibility(models.TextChoices):
        PUBLIC  = 'public',  'Public'   # visible to all workspace members
        PRIVATE = 'private', 'Private'  # visible only to project members

    workspace   = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status      = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    visibility  = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    lead        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='led_projects',
    )

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        # Project names must be unique within a workspace
        unique_together = [('workspace', 'name')]

    def __str__(self):
        return f'{self.workspace.name} / {self.name}'