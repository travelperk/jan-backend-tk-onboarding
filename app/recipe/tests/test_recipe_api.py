from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core.models import Recipe, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 22,
        "price": 5.25,
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class TestPublicRecipeAPI:
    """Test unauthenticated recipe API access"""

    def test_auth_required(self, api_client):
        """Test that authentication is required"""
        res = api_client.get(RECIPES_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestPrivateRecipeAPI:
    """Test authenticated recipe API access"""

    @pytest.mark.django_db
    def test_retrieve_recipes(self, api_client, api_authenticated_user):
        """Test retrieving a list of recipes"""
        create_recipe(user=api_authenticated_user)
        create_recipe(user=api_authenticated_user)

        res = api_client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_get_recipe_detail(self, api_client, api_authenticated_user):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=api_authenticated_user)

        url = detail_url(recipe.id)
        res = api_client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        assert res.data == serializer.data

    @pytest.mark.django_db
    def test_create_recipe(self, api_client, api_authenticated_user):
        """Test creating recipe"""
        payload = {
            "title": "Sample recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }
        res = api_client.post(RECIPES_URL, payload)

        assert res.status_code == status.HTTP_201_CREATED
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload:
            assert payload[key] == getattr(recipe, key)
        assert recipe.user == api_authenticated_user

    @pytest.mark.django_db
    def test_partial_update_recipe(self, api_client, api_authenticated_user):
        """Test updating a recipe with patch"""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=api_authenticated_user, title="Sample title", link=original_link
        )
        url = detail_url(recipe.id)
        payload = {"title": "New title"}
        res = api_client.patch(url, payload)

        assert res.status_code == status.HTTP_200_OK
        recipe.refresh_from_db()
        assert recipe.title == payload["title"]
        assert recipe.link == original_link

    @pytest.mark.django_db
    def test_full_update(self, api_client, api_authenticated_user):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=api_authenticated_user,
            title="Sample title",
            link="http://example.com/recipe.pdf",
            description="Sample description",
        )

        payload = {
            "title": "New title",
            "time_minutes": 10,
            "price": Decimal("2.50"),
            "link": "http://example.com/new-recipe.pdf",
            "description": "New description",
        }
        url = detail_url(recipe.id)
        res = api_client.put(url, payload)

        assert res.status_code == status.HTTP_200_OK
        recipe.refresh_from_db()
        for key in payload:
            assert payload[key] == getattr(recipe, key)
        assert recipe.user == api_authenticated_user

    @pytest.mark.django_db
    def test_update_user_does_nothing(self, api_client, api_authenticated_user):
        """Test that user cannot be updated"""
        new_user = get_user_model().objects.create(email="user2@example.com", password="test123")
        recipe = create_recipe(user=api_authenticated_user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        api_client.patch(url, payload)

        recipe.refresh_from_db()
        assert recipe.user == api_authenticated_user

    @pytest.mark.django_db
    def test_delete_recipe(self, api_client, api_authenticated_user):
        """Test deleting a recipe successful"""
        recipe = create_recipe(user=api_authenticated_user)
        url = detail_url(recipe.id)

        res = api_client.delete(url)

        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Recipe.objects.filter(id=recipe.id).exists()

    @pytest.mark.django_db
    def test_recipe_other_users_recipe_error(self, api_client, api_authenticated_user):
        """Test that user cannot delete other users recipe"""
        new_user = get_user_model().objects.create(email="user2@example.com", password="test123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = api_client.delete(url)

        assert res.status_code == status.HTTP_404_NOT_FOUND
        assert Recipe.objects.filter(id=recipe.id).exists()

    @pytest.mark.django_db
    def test_create_recipe_with_new_tags(self, api_client, api_authenticated_user):
        """Test creating a recipe with new tags"""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }
        res = api_client.post(RECIPES_URL, payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        recipes = Recipe.objects.filter(user=api_authenticated_user)
        assert recipes.count() == 1
        tags = recipes.first().tags.all()
        assert tags.count() == 2

        assert tags[0].name == payload["tags"][0]["name"]
        assert tags[1].name == payload["tags"][1]["name"]

    @pytest.mark.django_db
    def test_create_recipe_with_existing_tags(self, api_client, api_authenticated_user):
        """Test creating a recipe with existing tags"""
        Tag.objects.create(user=api_authenticated_user, name="Indian")
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("4.50"),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
        }
        res = api_client.post(RECIPES_URL, payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        recipes = Recipe.objects.filter(user=api_authenticated_user)
        assert recipes.count() == 1
        recipe = recipes.first()
        assert recipe.tags.count() == 2
        assert list(recipe.tags.values("name")) == payload["tags"]

    @pytest.mark.django_db
    def test_create_tag_on_update(self, api_client, api_authenticated_user):
        recipe = create_recipe(user=api_authenticated_user)
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = api_client.patch(url, payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        new_tag = Tag.objects.get(user=api_authenticated_user, name="Lunch")
        assert new_tag in recipe.tags.all()

    @pytest.mark.django_db
    def test_update_recipe_assign_tag(self, api_client, api_authenticated_user):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=api_authenticated_user, name="Breakfast")
        recipe = create_recipe(user=api_authenticated_user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=api_authenticated_user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = api_client.patch(url, payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        assert tag_lunch in recipe.tags.all()
        assert tag_breakfast not in recipe.tags.all()

    @pytest.mark.django_db
    def test_clear_recipe_tags(self, api_client, api_authenticated_user):
        """Test clearing all tags from a recipe"""
        tag = Tag.objects.create(user=api_authenticated_user, name="Dessert")
        recipe = create_recipe(user=api_authenticated_user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = api_client.patch(url, payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        assert recipe.tags.count() == 0
