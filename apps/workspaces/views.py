from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsWorkspaceAdminOrOwner, IsWorkspaceOwner
from .models import Workspace, WorkspaceMember
from .serializers import (
    InviteMemberSerializer,
    UpdateMemberRoleSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)


class WorkspaceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/workspaces/       — list workspaces the user belongs to
    POST /api/workspaces/       — create a new workspace
    """
    serializer_class   = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return workspaces the requesting user is a member of
        return Workspace.objects.filter(
            members__user=self.request.user
        ).select_related('owner').prefetch_related('members')


class WorkspaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/workspaces/<id>/  — retrieve
    PATCH  /api/workspaces/<id>/  — update (admin/owner only)
    DELETE /api/workspaces/<id>/  — delete (owner only)
    """
    serializer_class   = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ['get', 'patch', 'delete']

    def get_queryset(self):
        return Workspace.objects.filter(members__user=self.request.user)

    def update(self, request, *args, **kwargs):
        workspace = self.get_object()
        self.check_object_permissions(request, workspace)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can edit the workspace.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        workspace = self.get_object()
        if not IsWorkspaceOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only the owner can delete the workspace.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class InviteMemberView(APIView):
    """POST /api/workspaces/<id>/invite/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        workspace = self._get_workspace_or_403(request, pk)
        if isinstance(workspace, Response):
            return workspace

        serializer = InviteMemberSerializer(
            data=request.data,
            context={'workspace': workspace, 'request': request},
        )
        serializer.is_valid(raise_exception=True)
        invite = serializer.save()

        return Response({
            'status':  'success',
            'message': f'Invite sent to {invite.email}.',
            'token':   invite.token,   # in prod, this goes in the email
        }, status=status.HTTP_201_CREATED)

    def _get_workspace_or_403(self, request, pk):
        try:
            workspace = Workspace.objects.get(pk=pk, members__user=request.user)
        except Workspace.DoesNotExist:
            return Response(
                {'detail': 'Workspace not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can invite members.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return workspace


class MemberListView(generics.ListAPIView):
    """GET /api/workspaces/<id>/members/"""
    serializer_class   = WorkspaceMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WorkspaceMember.objects.filter(
            workspace_id=self.kwargs['pk'],
            workspace__members__user=self.request.user,
        ).select_related('user')


class UpdateMemberRoleView(APIView):
    """PUT /api/workspaces/<id>/members/<user_id>/"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk, user_id):
        workspace = Workspace.objects.filter(
            pk=pk, members__user=request.user
        ).first()
        if not workspace:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response(
                {'detail': 'Only admins and owners can change roles.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        member = WorkspaceMember.objects.filter(
            workspace=workspace, user_id=user_id
        ).first()
        if not member:
            return Response(
                {'detail': 'Member not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if member.role == WorkspaceMember.Role.OWNER:
            return Response(
                {'detail': "Cannot change the owner's role."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member.role = serializer.validated_data['role']
        member.save()

        return Response(WorkspaceMemberSerializer(member).data)


class RemoveMemberView(APIView):
    """DELETE /api/workspaces/<id>/members/<user_id>/"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, user_id):
        workspace = Workspace.objects.filter(
            pk=pk, members__user=request.user
        ).first()
        if not workspace:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Members can remove themselves; admins/owners can remove others
        is_self = str(request.user.id) == str(user_id)
        if not is_self and not IsWorkspaceAdminOrOwner().has_object_permission(
            request, self, workspace
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        member = WorkspaceMember.objects.filter(
            workspace=workspace, user_id=user_id
        ).first()
        if not member:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if member.role == WorkspaceMember.Role.OWNER:
            return Response(
                {'detail': 'Cannot remove the workspace owner.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)