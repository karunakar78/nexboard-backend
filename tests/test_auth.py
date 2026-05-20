import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestRegister:
    url = '/api/auth/register/'

    def test_register_success(self, api_client):
        payload = {
            'email': 'new@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == 'new@test.com'

    def test_register_password_mismatch(self, api_client):
        payload = {
            'email': 'new@test.com',
            'password': 'Str0ng!Pass',
            'password2': 'WrongPass!',
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client, user):
        payload = {
            'email': user.email,   # already exists
            'password': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        payload = {
            'email': 'weak@test.com',
            'password': '123',
            'password2': '123',
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    url = '/api/auth/token/'

    def test_login_success(self, api_client, user):
        response = api_client.post(self.url, {
            'email': user.email,
            'password': 'Str0ng!Pass',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(self.url, {
            'email': user.email,
            'password': 'WrongPassword!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(self.url, {
            'email': 'ghost@test.com',
            'password': 'Str0ng!Pass',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfile:
    url = '/api/auth/profile/'

    def test_get_profile_authenticated(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['full_name'] is not None

    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, auth_client):
        response = auth_client.patch(self.url, {'first_name': 'Updated'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'

    def test_cannot_update_email(self, auth_client, user):
        """Email is read-only — changing it should have no effect."""
        original_email = user.email
        auth_client.patch(self.url, {'email': 'hacked@test.com'})
        user.refresh_from_db()
        assert user.email == original_email


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_token(self, api_client, user):
        # Login to get tokens
        login = api_client.post('/api/auth/token/', {
            'email': user.email,
            'password': 'Str0ng!Pass',
        })
        refresh_token = login.data['refresh']
        access_token  = login.data['access']

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.post('/api/auth/logout/', {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK

        # Try to use the blacklisted refresh token
        response = api_client.post('/api/auth/token/refresh/', {'refresh': refresh_token})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED