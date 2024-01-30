import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core import models
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


@pytest.mark.django_db
class TestPublicTagsApi:
    """Test the publicly available tags API"""

    def test_login_required(self, api_client):
        """Test that login is required for retrieving tags"""
        response = api_client.get(TAGS_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateTagsApi:
    """Test the authorized user tags API"""

    def test_retrieve_tags(self, api_client, api_authenticated_user):
        """Test retrieving tags"""
        models.Tag.objects.create(user=api_authenticated_user, name="Vegan")
        models.Tag.objects.create(user=api_authenticated_user, name="Dessert")

        res = api_client.get(TAGS_URL)
        assert res.status_code == status.HTTP_200_OK

        tags = models.Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        assert res.data == serializer.data

    def test_tags_limited_to_user(self, api_client, api_authenticated_user):
        """Test that tags returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user("user2@example.com", "testpass")
        models.Tag.objects.create(user=user2, name="Fruity")
        tag = models.Tag.objects.create(user=api_authenticated_user, name="Comfort Food")

        res = api_client.get(TAGS_URL)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["id"] == tag.id
        assert res.data[0]["name"] == tag.name

    def test_update_tag_successful(self, api_client, api_authenticated_user):
        """Test updating a tag"""
        tag = models.Tag.objects.create(user=api_authenticated_user, name="Test Tag")

        payload = {"name": "New Tag Name"}
        url = reverse("recipe:tag-detail", args=[tag.id])
        res = api_client.patch(url, payload)

        tag.refresh_from_db()
        assert res.status_code == status.HTTP_200_OK
        assert tag.name == payload["name"]

    def test_delete_tag_successful(self, api_client, api_authenticated_user):
        """Test deleting a tag"""
        tag = models.Tag.objects.create(user=api_authenticated_user, name="Breakfast")
        url = reverse("recipe:tag-detail", args=[tag.id])
        res = api_client.delete(url)

        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not models.Tag.objects.filter(id=tag.id).exists()
