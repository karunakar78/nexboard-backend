from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Workspace(TimeStampedModel):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True, max_length=120)
    description = models.TextField(blank=True)
    owner       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces',
    )

    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WorkspaceMember(TimeStampedModel):
    """
    Junction table between User and Workspace.
    Stores the role so we know what a member is allowed to do.
    """
    class Role(models.TextChoices):
        OWNER  = 'owner',  'Owner'
        ADMIN  = 'admin',  'Admin'
        MEMBER = 'member', 'Member'
        GUEST  = 'guest',  'Guest'

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships',
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    class Meta:
        db_table = 'workspace_members'
        # A user can only have one role per workspace
        unique_together = [('workspace', 'user')]

    def __str__(self):
        return f'{self.user.email} — {self.workspace.name} ({self.role})'


class WorkspaceInvite(TimeStampedModel):
    """
    Pending email invitations. Token is checked when the invitee clicks
    the link. Expires after 7 days.
    """
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        EXPIRED  = 'expired',  'Expired'

    workspace   = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invites',
    )
    invited_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invites',
    )
    email       = models.EmailField()
    role        = models.CharField(
        max_length=10,
        choices=WorkspaceMember.Role.choices,
        default=WorkspaceMember.Role.MEMBER,
    )
    token       = models.CharField(max_length=64, unique=True)
    status      = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    expires_at  = models.DateTimeField()

    class Meta:
        db_table = 'workspace_invites'
        unique_together = [('workspace', 'email')]

    def __str__(self):
        return f'Invite → {self.email} to {self.workspace.name}'