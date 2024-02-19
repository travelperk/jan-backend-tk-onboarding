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
        user2 = get_user_model().objects.create_user("user2@example.com", "3pEm4AJoDU6xt")
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

    def test_filter_tags_assigned_to_recipes(self, api_client, api_authenticated_user):
        """Test filtering tags by those assigned to recipes"""
        tag1 = models.Tag.objects.create(user=api_authenticated_user, name="Breakfast")
        tag2 = models.Tag.objects.create(user=api_authenticated_user, name="Lunch")
        recipe = models.Recipe.objects.create(
            user=api_authenticated_user, title="Green eggs on toast", time_minutes=10, price=2.5
        )
        recipe.tags.add(tag1)

        res = api_client.get(TAGS_URL, {"assigned_only": 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    def test_filter_tags_assigned_unique(self, api_client, api_authenticated_user):
        """Test filtering tags by assigned returns unique items"""
        tag = models.Tag.objects.create(user=api_authenticated_user, name="Breakfast")
        models.Tag.objects.create(user=api_authenticated_user, name="Lunch")
        recipe1 = models.Recipe.objects.create(
            user=api_authenticated_user, title="Pancakes", time_minutes=5, price=3.0
        )
        recipe1.tags.add(tag)
        recipe2 = models.Recipe.objects.create(
            user=api_authenticated_user, title="Porridge", time_minutes=3, price=2.0
        )
        recipe2.tags.add(tag)

        res = api_client.get(TAGS_URL, {"assigned_only": 1})
        assert len(res.data) == 1
