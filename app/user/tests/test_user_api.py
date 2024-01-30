import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user_helper(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


@pytest.mark.django_db
class TestPublicUserApi:
    """Test the public features of the user API"""

    def test_create_user_success(self, api_client):
        """Test creating a user is successful."""
        payload = {
            "email": "test@example.com",
            "password": "test123",
            "name": "Test Name",
        }
        res = api_client.post(CREATE_USER_URL, payload)

        assert res.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(email=payload["email"])
        assert user.check_password(payload["password"]) is True

    def test_user_with_email_exists(self, api_client):
        """Test error returned if user with email exists."""
        payload = {"email": "test@example.com", "password": "test123", "name": "Test Name"}
        create_user_helper(**payload)
        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_for_user(self, api_client):
        """Test generates token for valid credentials"""
        user_details = {"email": "test@example.com", "password": "test123", "name": "Test Name"}
        create_user_helper(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }
        res = api_client.post(TOKEN_URL, payload)

        assert res.status_code == status.HTTP_200_OK
        assert "token" in res.data

    def test_create_token_bad_credentials(self, api_client):
        """Test returns error if credentials invalid"""
        create_user_helper(email="test@example.com", password="goodpass")

        payload = {"email": "test@example.com", "password": "badpass"}
        res = api_client.post(TOKEN_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" not in res.data

    def test_create_token_empty_credentials(self, api_client):
        """Test returns error if credentials empty"""
        payload = {"email": "test@example.com", "password": ""}
        res = api_client.post(TOKEN_URL, payload)

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" not in res.data

    def test_retrieve_user_unauthorized(self, api_client):
        """Test authentication is required for users"""
        res = api_client.get(ME_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateUserApi:
    """Test API requests that require authentication"""

    def test_retrieve_profile_success(self, api_client, api_authenticated_user):
        """Test retrieving profile for logged in user"""
        res = api_client.get(ME_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == {
            "name": api_authenticated_user.name,
            "email": api_authenticated_user.email,
        }

    def test_post_me_not_allowed(self, api_client, api_authenticated_user):
        """Test that post method is not allowed on me endpoint"""
        res = api_client.post(ME_URL, {})
        assert res.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_user_profile(self, api_client, api_authenticated_user):
        """Test updating the user profile for the authenticated user"""
        payload = {"name": "Updated name", "password": "newpassword"}
        res = api_client.patch(ME_URL, payload)

        assert res.status_code == status.HTTP_200_OK
        api_authenticated_user.refresh_from_db()
        assert api_authenticated_user.name == payload["name"]
        assert api_authenticated_user.check_password(payload["password"])
