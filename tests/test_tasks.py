import pytest
from rest_framework import status
from apps.workspaces.models import WorkspaceMember
from apps.tasks.models import Task, ActivityLog


@pytest.mark.django_db
class TestTaskCreate:

    def test_create_task_success(self, auth_client, workspace, project):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/',
            {
                'title': 'New Task',
                'priority': 'high',
                'status': 'todo',
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
        assert response.data['comment_count'] == 0

    def test_task_creation_logs_activity(self, auth_client, workspace, project):
        """Every new task must have an activity log entry."""
        auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/',
            {'title': 'Logged Task', 'status': 'todo', 'priority': 'low'},
        )
        task = Task.objects.get(title='Logged Task')
        assert ActivityLog.objects.filter(task=task, verb='created this task').exists()

    def test_non_member_cannot_create_task(self, other_auth_client, workspace, project):
        response = other_auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/',
            {'title': 'Hacked Task', 'status': 'todo', 'priority': 'low'},
        )
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.django_db
class TestTaskUpdate:

    def test_update_task_status_logs_activity(self, auth_client, workspace, project, task):
        auth_client.patch(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
            {'status': 'done'},
        )
        task.refresh_from_db()
        assert task.status == Task.Status.DONE
        assert ActivityLog.objects.filter(
            task=task,
            verb__contains='status',
        ).exists()

    def test_update_task_priority(self, auth_client, workspace, project, task):
        response = auth_client.patch(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
            {'priority': 'urgent'},
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.priority == Task.Priority.URGENT


@pytest.mark.django_db
class TestTaskDelete:

    def test_creator_can_delete_task(self, auth_client, workspace, project, task):
        response = auth_client.delete(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_creator_member_cannot_delete_task(
        self, api_client, workspace, project, task, other_user
    ):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.MEMBER,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any_task(self, api_client, workspace, project, task, other_user):
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=other_user,
            role=WorkspaceMember.Role.ADMIN,
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestSubtasks:

    def test_create_subtask(self, auth_client, workspace, project, task):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/',
            {
                'title': 'Subtask',
                'status': 'todo',
                'priority': 'low',
                'parent': str(task.id),
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        subtask = Task.objects.get(title='Subtask')
        assert subtask.parent == task
        assert subtask.is_subtask is True

    def test_parent_task_shows_subtasks(self, auth_client, workspace, project, task):
        Task.objects.create(
            project=project,
            title='Child Task',
            parent=task,
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
            created_by=None,
        )
        response = auth_client.get(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/',
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['subtasks']) == 1
        assert response.data['subtasks'][0]['title'] == 'Child Task'


@pytest.mark.django_db
class TestComments:

    def test_add_comment(self, auth_client, workspace, project, task):
        response = auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/comments/',
            {'content': 'This is a comment'},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'This is a comment'
        assert response.data['author']['email'] == 'test@test.com'

    def test_list_comments(self, auth_client, workspace, project, task):
        auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/comments/',
            {'content': 'First comment'},
        )
        auth_client.post(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/comments/',
            {'content': 'Second comment'},
        )
        response = auth_client.get(
            f'/api/workspaces/{workspace.id}/projects/{project.id}/tasks/{task.id}/comments/',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2