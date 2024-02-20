from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from core import models

DEFAULT_PASS = "Mmf3pEm4AJ"


@pytest.mark.django_db
def test_create_user_with_email_successful():
    """Test creating a user with an email is successful"""
    email = "valid@email.com"
    password = DEFAULT_PASS
    get_user_model().objects.create_user(email=email, password=password)

    user = get_user_model().objects.first()
    assert user.email == email
    assert user.check_password(password) is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "original,normalised",
    (
        ("test1@EXAMPLE.com", "test1@example.com"),
        ("Test2@Example.com", "Test2@example.com"),
        ("TEST3@EXAMPLE.COM", "TEST3@example.com"),
        ("test4@example.COM", "test4@example.com"),
    ),
)
def test_new_user_email_normalized(original, normalised):
    """Test email is normalized for new users"""
    get_user_model().objects.create_user(original, DEFAULT_PASS)
    user = get_user_model().objects.first()
    assert user.email == normalised


@pytest.mark.django_db
def test_new_user_without_email_raises_error():
    """User without an email raises a ValueError."""
    with pytest.raises(ValueError):
        get_user_model().objects.create_user("", DEFAULT_PASS)


@pytest.mark.django_db
def test_create_superuser():
    """Test creating a superuser."""
    get_user_model().objects.create_superuser("test@example.com", DEFAULT_PASS)
    user = get_user_model().objects.first()
    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.check_password(DEFAULT_PASS) is True


@pytest.mark.django_db
def test_user_can_log_in():
    """Test user can log in"""
    get_user_model().objects.create_user("test@example.com", DEFAULT_PASS)
    user = get_user_model().objects.first()
    assert user.check_password(DEFAULT_PASS) is True


@pytest.mark.django_db
def test_create_recipe(user):
    """Test creating a recipe"""
    recipe = models.Recipe.objects.create(
        user=user,
        title="Test recipe",
        time_minutes=5,
        price=5.50,
        description="Sample recipe description",
    )

    assert str(recipe) == recipe.title


@pytest.mark.django_db
def test_create_tag(user):
    """Test creating a tag"""
    tag = models.Tag.objects.create(
        user=user,
        name="Test tag",
    )

    assert str(tag) == tag.name


@pytest.mark.django_db
def test_create_ingredients(user):
    """Test creating an ingredient"""
    ingredient = models.Ingredient.objects.create(
        user=user,
        name="Test ingredient",
    )

    assert str(ingredient) == ingredient.name


@pytest.mark.django_db
@patch("core.models.uuid.uuid4")
def test_recipe_file_name_uuid(mock_uuid):
    """Test generating image path"""
    uuid = "test-uuid"
    mock_uuid.return_value = uuid
    file_path = models.recipe_image_file_path(None, "example.jpg")

    assert file_path == f"uploads/recipe/{uuid}.jpg"
