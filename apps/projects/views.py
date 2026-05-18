from rest_framework import generics, permissions, status
from rest_framework.response import Response

from common.permissions import IsWorkspaceAdminOrOwner
from apps.workspaces.models import Workspace, WorkspaceMember
from .models import Project
from .serializers import ProjectSerializer


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/workspaces/<ws_id>/projects/  — list projects user can see
    POST /api/workspaces/<ws_id>/projects/  — create project (admin/owner)
    """
    serializer_class   = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_workspace(self):
        return Workspace.objects.filter(
            pk=self.kwargs['ws_id'],
            members__user=self.request.user,
        ).first()

    def get_queryset(self):
        workspace = self.get_workspace()
        if not workspace:
            return Project.objects.none()

        membership = WorkspaceMember.objects.filter(
            workspace=workspace, user=self.request.user
        ).first()

        qs = Project.objects.filter(workspace=workspace).select_related('lead')

        # Guests and plain members only see public projects
        if membership and membership.role in [
            WorkspaceMember.Role.GUEST,
            WorkspaceMember.Role.MEMBER,
        ]:
            qs = qs.filter(visibility=Project.Visibility.PUBLIC)

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['workspace'] = self.get_workspace()
        return ctx

    def create(self, request, *args, **kwargs):
        workspace = self.get_workspace()
        if not workspace:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can create projects.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/workspaces/<ws_id>/projects/<id>/
    PATCH  /api/workspaces/<ws_id>/projects/<id>/  — admin/owner only
    DELETE /api/workspaces/<ws_id>/projects/<id>/  — admin/owner only
    """
    serializer_class   = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ['get', 'patch', 'delete']

    def get_workspace(self):
        return Workspace.objects.filter(
            pk=self.kwargs['ws_id'],
            members__user=self.request.user,
        ).first()

    def get_queryset(self):
        workspace = self.get_workspace()
        if not workspace:
            return Project.objects.none()
        return Project.objects.filter(workspace=workspace).select_related('lead')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['workspace'] = self.get_workspace()
        return ctx

    def update(self, request, *args, **kwargs):
        workspace = self.get_workspace()
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can edit projects.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        workspace = self.get_workspace()
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can delete projects.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)