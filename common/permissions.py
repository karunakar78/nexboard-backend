from rest_framework.permissions import BasePermission

from apps.workspaces.models import WorkspaceMember


def get_membership(user, workspace):
    return WorkspaceMember.objects.filter(
        workspace=workspace, user=user
    ).first()


class IsWorkspaceMember(BasePermission):
    """Allow any member (any role) of the workspace."""
    def has_object_permission(self, request, view, obj):
        return get_membership(request.user, obj) is not None


class IsWorkspaceAdminOrOwner(BasePermission):
    """Only owner or admin can perform the action."""
    def has_object_permission(self, request, view, obj):
        membership = get_membership(request.user, obj)
        if not membership:
            return False
        return membership.role in [
            WorkspaceMember.Role.OWNER,
            WorkspaceMember.Role.ADMIN,
        ]


class IsWorkspaceOwner(BasePermission):
    """Only the workspace owner can perform the action."""
    def has_object_permission(self, request, view, obj):
        membership = get_membership(request.user, obj)
        if not membership:
            return False
        return membership.role == WorkspaceMember.Role.OWNER