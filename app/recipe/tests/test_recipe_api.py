import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")
DEFAULT_PASS = "3pEm4AJoDU6xt"


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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
        new_user = get_user_model().objects.create(
            email="user2@example.com", password=DEFAULT_PASS
        )
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
        new_user = get_user_model().objects.create(
            email="user2@example.com", password=DEFAULT_PASS
        )
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

    @pytest.mark.django_db
    def test_create_recipe_with_new_ingredients(self, api_client, api_authenticated_user):
        """Test creating a recipe with new ingredients."""
        payload = {
            "title": "Cauliflower Tacos",
            "time_minutes": 60,
            "price": Decimal("4.30"),
            "ingredients": [{"name": "Cauliflower"}, {"name": "Salt"}],
        }
        res = api_client.post(RECIPES_URL, payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()
        assert ingredients.count() == 2
        assert ingredients[0].name == payload["ingredients"][0]["name"]
        assert ingredients[1].name == payload["ingredients"][1]["name"]

    @pytest.mark.django_db
    def test_create_recipe_with_existing_ingredients(self, api_client, api_authenticated_user):
        """Test creating a recipe with existing ingredients."""
        ingredient_name = "Cauliflower"
        Ingredient.objects.create(user=api_authenticated_user, name=ingredient_name)

        payload = {
            "title": "Cauliflower Tacos",
            "time_minutes": 60,
            "price": Decimal("4.30"),
            "ingredients": [{"name": ingredient_name}, {"name": "Salt"}],
        }
        res = api_client.post(RECIPES_URL, payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        assert Ingredient.objects.count() == 2
        assert payload["ingredients"] == list(Recipe.objects.first().ingredients.values("name"))

    @pytest.mark.django_db
    def test_update_recipe_update_ingredient(self, api_client, api_authenticated_user):
        """Test creating an ingredient on update."""
        recipe = create_recipe(user=api_authenticated_user)
        ingredients = [Ingredient.objects.create(user=api_authenticated_user, name="Cauliflower")]
        recipe.ingredients.set(ingredients)

        payload = {"ingredients": [{"name": "Salt"}]}
        url = detail_url(recipe.id)
        res = api_client.patch(url, payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        assert recipe.ingredients.count() == 1
        assert recipe.ingredients.first().name == "Salt"

    @pytest.mark.django_db
    def test_clear_recipe_ingredients(self, api_client, api_authenticated_user):
        """Test clearing all ingredients from a recipe."""
        recipe = create_recipe(user=api_authenticated_user)
        ingredients = [Ingredient.objects.create(user=api_authenticated_user, name="Cauliflower")]
        recipe.ingredients.set(ingredients)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = api_client.patch(url, payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        assert recipe.ingredients.count() == 0

    @pytest.mark.django_db
    def test_filter_by_tags(self, api_client, api_authenticated_user):
        """Test returning recipes with specific tags"""
        r1 = create_recipe(user=api_authenticated_user, title="Thai Vegetable Curry")
        r2 = create_recipe(user=api_authenticated_user, title="Aubergine with Tahini")

        # Recipes with tags
        tag1 = Tag.objects.create(user=api_authenticated_user, name="Vegan")
        tag2 = Tag.objects.create(user=api_authenticated_user, name="Vegetarian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        # Recipes without tags
        create_recipe(user=api_authenticated_user, title="Fish and chips")

        params = {"tags": f"{tag1.id},{tag2.id}"}
        res = api_client.get(RECIPES_URL, params)

        tagged_recipes = RecipeSerializer([r2, r1], many=True)

        assert res.status_code == status.HTTP_200_OK
        # Only expect the recipes with the tags to be returned
        assert tagged_recipes.data == res.data

    @pytest.mark.django_db
    def test_filter_by_ingredients(self, api_client, api_authenticated_user):
        """Test returning recipes with specific ingredients"""
        r1 = create_recipe(user=api_authenticated_user, title="Posh beans on toast")
        r2 = create_recipe(user=api_authenticated_user, title="Chicken Cacciatore")

        # Recipes with ingredients
        ingredient1 = Ingredient.objects.create(user=api_authenticated_user, name="Feta cheese")
        ingredient2 = Ingredient.objects.create(user=api_authenticated_user, name="Chicken")
        r1.ingredients.add(ingredient1)
        r2.ingredients.add(ingredient2)

        # Recipes without ingredients
        create_recipe(user=api_authenticated_user, title="Red Lentil Daal")

        params = {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        res = api_client.get(RECIPES_URL, params)

        ingredient_recipes = RecipeSerializer([r2, r1], many=True)

        assert res.status_code == status.HTTP_200_OK
        # Only expect the recipes with the ingredients to be returned
        assert ingredient_recipes.data == res.data


@pytest.mark.django_db
class TestImageUpload:
    """Tests for the image upload API"""

    @pytest.fixture
    def recipe(self, api_authenticated_user):
        recipe = create_recipe(user=api_authenticated_user)
        yield recipe
        recipe.image.delete()

    def test_upload_image(self, api_client, recipe):
        """Test uploading an image to a recipe"""
        url = image_upload_url(recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            image = Image.new("RGB", (10, 10))
            image.save(image_file, format="JPEG")
            image_file.seek(0)

            payload = {"image": image_file}
            res = api_client.post(url, payload, format="multipart")

        recipe.refresh_from_db()
        assert res.status_code == status.HTTP_200_OK
        assert "image" in res.data
        assert Path(recipe.image.path).exists()

    def test_upload_image_bad_request(self, api_client, recipe):
        """Test uploading invalid image."""
        url = image_upload_url(recipe.id)
        res = api_client.post(url, {"image": "notanimage"}, format="multipart")

        assert res.status_code == status.HTTP_400_BAD_REQUEST
