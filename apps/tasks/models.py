from django.conf import settings
from django.db import models

from common.models import TimeStampedModel
from apps.projects.models import Project


class Label(TimeStampedModel):
    """Reusable labels scoped to a project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    name    = models.CharField(max_length=50)
    color   = models.CharField(max_length=7, default='#6366f1')  # hex color

    class Meta:
        db_table = 'labels'
        unique_together = [('project', 'name')]

    def __str__(self):
        return f'{self.project.name} / {self.name}'


class Task(TimeStampedModel):

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        BACKLOG     = 'backlog',     'Backlog'
        TODO        = 'todo',        'Todo'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW   = 'in_review',   'In Review'
        DONE        = 'done',        'Done'
        CANCELLED   = 'cancelled',   'Cancelled'

    project     = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assignee    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tasks',
    )
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
    )
    labels      = models.ManyToManyField(Label, blank=True, related_name='tasks')
    due_date    = models.DateField(null=True, blank=True)
    # Self-referential FK for subtasks
    parent      = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subtasks',
    )

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_subtask(self):
        return self.parent_id is not None


class Comment(TimeStampedModel):
    task    = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.email} on {self.task.title}'


class ActivityLog(TimeStampedModel):
    """
    Immutable record of every change made to a task.
    Written automatically in the view/serializer, never edited.
    """
    task       = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activity')
    actor      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activities')
    verb       = models.CharField(max_length=100)   # e.g. "changed status to done"
    old_value  = models.CharField(max_length=255, blank=True)
    new_value  = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor} {self.verb}'