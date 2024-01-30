import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture()
def authenticated_admin(client):
    admin = get_user_model().objects.create_superuser(
        email="admin@example.com", password="test123", name="Test Admin"
    )

    client.force_login(admin)
    return admin


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="test@example.com",
        password="test123",
    )


@pytest.fixture
def api_authenticated_user(user, api_client):
    api_client.force_authenticate(user=user)
    return user
