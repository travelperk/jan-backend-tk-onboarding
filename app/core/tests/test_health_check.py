from django.urls import reverse


def test_health_check(api_client):
    """Test health check endpoint."""
    url = reverse("health-check")
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
