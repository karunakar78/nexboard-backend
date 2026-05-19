from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.projects.models import Project
from apps.workspaces.models import WorkspaceMember
from .models import ActivityLog, Comment, Label, Task
from .serializers import (
    ActivityLogSerializer, CommentSerializer,
    LabelSerializer, TaskSerializer,
)
from apps.notifications.tasks import (
    create_in_app_notification,
    send_comment_notification_email,
    send_task_assigned_email,
)
from apps.notifications.models import Notification
from common.cache import invalidate_workspace_analytics


def get_project(ws_id, project_id, user):
    """Helper — returns project only if user is a workspace member."""
    return Project.objects.filter(
        pk=project_id,
        workspace_id=ws_id,
        workspace__members__user=user,
    ).select_related('workspace').first()


class LabelListCreateView(generics.ListCreateAPIView):
    serializer_class   = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project = get_project(self.kwargs['ws_id'], self.kwargs['project_id'], self.request.user)
        if not project:
            return Label.objects.none()
        return Label.objects.filter(project=project)

    def perform_create(self, serializer):
        project = get_project(self.kwargs['ws_id'], self.kwargs['project_id'], self.request.user)
        serializer.save(project=project)


class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET  — list tasks with filtering by status, priority, assignee
    POST — create task (any workspace member)
    """
    serializer_class   = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields   = ['status', 'priority', 'assignee']
    search_fields      = ['title', 'description']
    ordering_fields    = ['created_at', 'due_date', 'priority']

    def get_project(self):
        return get_project(
            self.kwargs['ws_id'], self.kwargs['project_id'], self.request.user
        )

    def get_queryset(self):
        project = self.get_project()
        if not project:
            return Task.objects.none()
        return Task.objects.filter(
            project=project,
            parent=None,   # top-level tasks only; subtasks come via parent
        ).select_related('assignee', 'created_by').prefetch_related('labels', 'subtasks')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['project'] = self.get_project()
        return ctx
    
    def perform_create(self, serializer):
        task = serializer.save()

        invalidate_workspace_analytics(task.project.workspace_id)

        # Fire async email if task has an assignee
        if task.assignee and task.assignee != self.request.user:
            send_task_assigned_email.delay(
                assignee_email=task.assignee.email,
                task_title=task.title,
                project_name=task.project.name,
                assigner_name=self.request.user.full_name,
            )
            create_in_app_notification.delay(
                recipient_id=str(task.assignee.id),
                notif_type=Notification.Type.TASK_ASSIGNED,
                title=f'You were assigned: {task.title}',
                body=f'In project {task.project.name}',
            )


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ['get', 'patch', 'delete']

    def get_project(self):
        return get_project(
            self.kwargs['ws_id'], self.kwargs['project_id'], self.request.user
        )

    def get_queryset(self):
        project = self.get_project()
        if not project:
            return Task.objects.none()
        return Task.objects.filter(project=project).select_related(
            'assignee', 'created_by'
        ).prefetch_related('labels', 'subtasks', 'comments')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['project'] = self.get_project()
        return ctx

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        # Only creator, assignee, or workspace admin/owner can delete
        membership = WorkspaceMember.objects.filter(
            workspace=task.project.workspace, user=request.user
        ).first()
        is_privileged = membership and membership.role in [
            WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN
        ]
        if not is_privileged and task.created_by != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_task(self):
        return Task.objects.filter(
            pk=self.kwargs['task_id'],
            project__workspace__members__user=self.request.user,
        ).first()

    def get_queryset(self):
        task = self.get_task()
        return Comment.objects.filter(task=task).select_related('author') if task else Comment.objects.none()

    def perform_create(self, serializer):
        task = self.get_task()
        comment = serializer.save(author=self.request.user, task=task)

        ActivityLog.objects.create(
            task=task,
            actor=self.request.user,
            verb='added a comment',
        )

        # Notify task assignee if it's not the commenter
        if task.assignee and task.assignee != self.request.user:
            send_comment_notification_email.delay(
                recipient_email=task.assignee.email,
                commenter_name=self.request.user.full_name,
                task_title=task.title,
            )
            create_in_app_notification.delay(
                recipient_id=str(task.assignee.id),
                notif_type=Notification.Type.TASK_COMMENTED,
                title=f'New comment on: {task.title}',
                body=comment.content[:100],
            )
        return comment


class ActivityLogListView(generics.ListAPIView):
    serializer_class   = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task = Task.objects.filter(
            pk=self.kwargs['task_id'],
            project__workspace__members__user=self.request.user,
        ).first()
        return ActivityLog.objects.filter(task=task).select_related('actor') if task else ActivityLog.objects.none()