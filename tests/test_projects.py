import pytest
from rest_framework import status
from apps.workspaces.models import WorkspaceMember
from apps.projects.models import Project


@pytest.mark.django_db
class TestProjectCreate:

    def test_owner_can_create_project(self, auth_client, workspace):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/',
            {'name': 'New Project', 'visibility': 'public'},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Project'
        assert response.data['task_count'] == 0

    def test_member_cannot_create_project(self, api_client, workspace, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.post(
            f'/api/workspaces/{workspace.id}/projects/',
            {'name': 'Sneaky Project', 'visibility': 'public'},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_member_cannot_create_project(self, other_auth_client, workspace):
        response = other_auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/',
            {'name': 'Hacked Project'},
        )
        # Non-member gets 404 — they shouldn't even know the workspace exists
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_duplicate_project_name_in_workspace(self, auth_client, workspace, project):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/',
            {'name': project.name},   # same name as fixture
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProjectVisibility:

    def test_guest_cannot_see_private_project(self, api_client, workspace, other_user):
        Project.objects.create(
            workspace=workspace,
            name='Secret Project',
            visibility=Project.Visibility.PRIVATE,
        )
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.GUEST,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f'/api/workspaces/{workspace.id}/projects/')
        names = [p['name'] for p in response.data['results']]
        assert 'Secret Project' not in names

    def test_admin_can_see_private_project(self, api_client, workspace, other_user):
        Project.objects.create(
            workspace=workspace,
            name='Secret Project',
            visibility=Project.Visibility.PRIVATE,
        )
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.ADMIN,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f'/api/workspaces/{workspace.id}/projects/')
        names = [p['name'] for p in response.data['results']]
        assert 'Secret Project' in names