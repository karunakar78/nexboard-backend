from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.workspaces.models import Workspace, WorkspaceMember


class WorkspaceAnalyticsView(APIView):
    """
    GET /api/workspaces/<id>/analytics/

    Cached for 5 minutes per user.
    vary_on_headers('Authorization') ensures each user gets their own cache entry
    — without it, user A's cached response could be served to user B.
    """
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request, pk):
        workspace = Workspace.objects.filter(
            pk=pk, members__user=request.user
        ).first()
        if not workspace:
            return Response({'detail': 'Not found.'}, status=404)

        projects = Project.objects.filter(workspace=workspace)
        tasks    = Task.objects.filter(project__workspace=workspace)

        # Task breakdown by status
        status_breakdown = {}
        for status in Task.Status.values:
            status_breakdown[status] = tasks.filter(status=status).count()

        # Task breakdown by priority
        priority_breakdown = {}
        for priority in Task.Priority.values:
            priority_breakdown[priority] = tasks.filter(priority=priority).count()

        # Member contribution — how many tasks each member created
        member_stats = []
        for member in WorkspaceMember.objects.filter(workspace=workspace).select_related('user'):
            member_stats.append({
                'user':          member.user.email,
                'role':          member.role,
                'tasks_created': tasks.filter(created_by=member.user).count(),
                'tasks_assigned': tasks.filter(assignee=member.user).count(),
            })

        return Response({
            'workspace':          workspace.name,
            'total_projects':     projects.count(),
            'total_tasks':        tasks.count(),
            'completed_tasks':    tasks.filter(status=Task.Status.DONE).count(),
            'overdue_tasks':      tasks.filter(
                due_date__lt=__import__('datetime').date.today()
            ).exclude(status__in=[Task.Status.DONE, Task.Status.CANCELLED]).count(),
            'status_breakdown':   status_breakdown,
            'priority_breakdown': priority_breakdown,
            'member_stats':       member_stats,
        })