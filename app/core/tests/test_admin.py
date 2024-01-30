import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains


@pytest.mark.django_db
def test_users_list(client, authenticated_admin, user):
    """Test users are listed on page"""
    url = reverse("admin:core_user_changelist")
    res = client.get(url)

    assertContains(res, user.name)
    assertContains(res, user.email)


@pytest.mark.django_db
def test_edit_user_page(client, authenticated_admin, user):
    url = reverse("admin:core_user_change", args=[user.id])
    res = client.get(url)

    assert res.status_code == 200


@pytest.mark.django_db
def test_create_user_page(client, authenticated_admin):
    url = reverse("admin:core_user_add")
    res = client.get(url)

    assert res.status_code == 200
