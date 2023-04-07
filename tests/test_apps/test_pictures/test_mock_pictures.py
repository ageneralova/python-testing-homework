import json
from http import HTTPStatus

import httpretty
import pytest
import requests
from django.test import Client
from django.urls import reverse

from server.apps.identity.models import User
from tests.plugins.identity.user import RegData


@pytest.fixture()
def mock_photos():
    """Get photos from json_server."""
    return requests.get(
        'http://json-server/photos',
        timeout=3,
    ).json()


@pytest.mark.django_db()
@httpretty.activate  # type: ignore[misc]
def test_pictures_dashboard_content(
    db_user: 'RegData',
    client: Client,
    mock_photos,
) -> None:
    """Check dashboard content."""
    httpretty.register_uri(
        httpretty.GET,
        'https://jsonplaceholder.typicode.com/photos',
        body=json.dumps(mock_photos),
    )
    user = User.objects.get(email=db_user['email'])
    client.force_login(user)

    response = client.get(reverse('pictures:dashboard'))
    assert response.status_code == HTTPStatus.OK
    assert len(response.context['pictures']) == len(mock_photos)
    assert response.context['pictures'] == mock_photos
