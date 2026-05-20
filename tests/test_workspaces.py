import pytest
from rest_framework import status
from apps.workspaces.models import Workspace, WorkspaceMember


@pytest.mark.django_db
class TestWorkspaceCreate:
    url = '/api/workspaces/'

    def test_create_workspace_success(self, auth_client):
        response = auth_client.post(self.url, {
            'name': 'My Workspace',
            'description': 'Test',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'My Workspace'
        assert response.data['my_role'] == 'owner'
        # Creator is automatically added as owner member
        assert Workspace.objects.filter(name='My Workspace').exists()

    def test_create_workspace_unauthenticated(self, api_client):
        response = api_client.post(self.url, {'name': 'Hack'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_slug_auto_generated(self, auth_client):
        response = auth_client.post(self.url, {'name': 'My Cool Workspace'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['slug'] == 'my-cool-workspace'


@pytest.mark.django_db
class TestWorkspaceAccess:
    url = '/api/workspaces/'

    def test_user_only_sees_own_workspaces(self, auth_client, other_auth_client, workspace):
        """Other user should not see workspaces they're not a member of."""
        response = other_auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        ids = [w['id'] for w in response.data['results']]
        assert str(workspace.id) not in ids

    def test_member_sees_workspace(self, auth_client, workspace):
        response = auth_client.get(self.url)
        ids = [w['id'] for w in response.data['results']]
        assert str(workspace.id) in ids


@pytest.mark.django_db
class TestWorkspaceRoles:

    def test_member_cannot_delete_workspace(self, api_client, workspace, other_user):
        """A plain member must not be able to delete the workspace."""
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(f'/api/workspaces/{workspace.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_guest_cannot_delete_workspace(self, api_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.GUEST,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(f'/api/workspaces/{workspace.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_delete_workspace(self, auth_client, workspace):
        response = auth_client.delete(f'/api/workspaces/{workspace.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_admin_can_update_workspace(self, api_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.ADMIN,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(
            f'/api/workspaces/{workspace.id}/',
            {'description': 'Updated by admin'},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_member_cannot_update_workspace(self, api_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(
            f'/api/workspaces/{workspace.id}/',
            {'description': 'Sneaky update'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestWorkspaceInvite:

    def test_owner_can_invite(self, auth_client, workspace):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/invite/',
            {'email': 'newguy@test.com', 'role': 'member'},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data

    def test_member_cannot_invite(self, api_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.post(
            f'/api/workspaces/{workspace.id}/invite/',
            {'email': 'another@test.com', 'role': 'member'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_invite_existing_member(self, auth_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/invite/',
            {'email': other_user.email, 'role': 'member'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST