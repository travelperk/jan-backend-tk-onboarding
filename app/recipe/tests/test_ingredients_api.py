import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Return ingredient detail URL"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


class TestPublicIngredientsApi:
    """Test the publicly available ingredients API"""

    def test_auth_required(self, api_client):
        """Test that login is required to access the endpoint"""
        res = api_client.get(INGREDIENTS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPrivateIngredientsApi:
    """Test the private ingredients API"""

    def test_retrieve_ingredients(self, api_client, api_authenticated_user):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=api_authenticated_user, name="Kale")
        Ingredient.objects.create(user=api_authenticated_user, name="Vanilla")

        res = api_client.get(INGREDIENTS_URL)

        assert res.status_code == status.HTTP_200_OK

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        assert res.status_code == status.HTTP_200_OK
        assert res.data == serializer.data

    def test_ingredients_limited_to_user(self, api_client, api_authenticated_user):
        """Test list of ingredients is limited to authenticated user"""
        user2 = get_user_model().objects.create_user("user2@example.com", "testpass")
        Ingredient.objects.create(user=user2, name="Salt")
        Ingredient.objects.create(user=api_authenticated_user, name="Pepper")

        res = api_client.get(INGREDIENTS_URL)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["name"] == "Pepper"

    def test_update_ingredient(self, api_client, api_authenticated_user):
        """Test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=api_authenticated_user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        res = api_client.patch(url, payload)

        assert res.status_code == status.HTTP_200_OK
        ingredient.refresh_from_db()
        assert ingredient.name == payload["name"]

    def test_delete_ingredient(self, api_client, api_authenticated_user):
        """Test deleting an ingredient"""
        ingredient = Ingredient.objects.create(user=api_authenticated_user, name="Cilantro")

        url = detail_url(ingredient.id)
        res = api_client.delete(url)

        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not Ingredient.objects.filter(id=ingredient.id).exists()

    def test_filter_ingredients_assigned_to_recipes(self, api_client, api_authenticated_user):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=api_authenticated_user, name="Apples")
        ingredient2 = Ingredient.objects.create(user=api_authenticated_user, name="Turkey")
        recipe = Recipe.objects.create(
            user=api_authenticated_user, title="Apple crumble", time_minutes=5, price="4.50"
        )
        recipe.ingredients.add(ingredient1)

        res = api_client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        assert serializer1.data in res.data
        assert serializer2.data not in res.data

    def test_filter_ingredients_unique(self, api_client, api_authenticated_user):
        """Test filtering ingredients by assigned returns unique items"""
        ing = Ingredient.objects.create(user=api_authenticated_user, name="Eggs")
        Ingredient.objects.create(user=api_authenticated_user, name="Cheese")

        recipe1 = Recipe.objects.create(
            user=api_authenticated_user, title="Egg benedict", time_minutes=30, price=12.00
        )
        recipe2 = Recipe.objects.create(
            user=api_authenticated_user,
            title="Coriander eggs on toast",
            time_minutes=20,
            price=5.00,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = api_client.get(INGREDIENTS_URL, {"assigned_only": 1})

        assert len(res.data) == 1
