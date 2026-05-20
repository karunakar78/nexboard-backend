import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.projects.models import Project
from apps.tasks.models import Task


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(email='test@test.com', password='Str0ng!Pass', **kwargs):
        return User.objects.create_user(email=email, password=password, **kwargs)
    return make_user


@pytest.fixture
def user(create_user):
    return create_user()


@pytest.fixture
def other_user(create_user):
    return create_user(email='other@test.com')


@pytest.fixture
def auth_client(api_client, user):
    """Authenticated API client — use this for protected endpoints."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    api_client.force_authenticate(user=other_user)
    return api_client


@pytest.fixture
def workspace(user):
    ws = Workspace.objects.create(
        name='Test Workspace',
        slug='test-workspace',
        owner=user,
    )
    WorkspaceMember.objects.create(
        workspace=ws,
        user=user,
        role=WorkspaceMember.Role.OWNER,
    )
    return ws


@pytest.fixture
def project(workspace):
    return Project.objects.create(
        workspace=workspace,
        name='Test Project',
        visibility=Project.Visibility.PUBLIC,
    )


@pytest.fixture
def task(project, user):
    return Task.objects.create(
        project=project,
        title='Test Task',
        created_by=user,
        status=Task.Status.TODO,
        priority=Task.Priority.MEDIUM,
    )