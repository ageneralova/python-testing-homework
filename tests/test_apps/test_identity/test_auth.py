import json
from http import HTTPStatus

import httpretty
import pytest
import requests
from django.test import Client
from django.urls import reverse

from server.apps.identity.models import User
from tests.plugins.identity.user import RegistrationData, UserAssertion


@pytest.mark.django_db()
def test_registration_page_renders(client: Client) -> None:
    """Basic `get` method works."""
    response = client.get(reverse('identity:registration'))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db()
def test_valid_registration(
    client: Client,
    registration_data: 'RegistrationData',
    assert_correct_user: 'UserAssertion',
) -> None:
    """Test that registration works with correct user data."""
    response = client.post(
        reverse('identity:registration'),
        data=registration_data,
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response.get('Location') == reverse('identity:login')
    assert_correct_user(registration_data)


@pytest.mark.django_db()
def test_valid_login(
    client: Client,
    user_data: 'RegistrationData',
) -> None:
    """Test whether correct user can log in"""
    # Save User model.
    user = User(**user_data)
    user.save()

    # Get data for login.
    login_data = {
        'username': user_data['email'],
        'password': user_data['password'],
    }

    # Login.
    client.force_login(user)

    # Check user login.
    response = client.post(
        reverse('identity:login'),
        data=login_data,
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.get('Location') == reverse('pictures:dashboard')


@pytest.fixture()
def mock_server_users(registration_data):
    """Get photos from json_server."""
    registration_data['date_of_birth'] = str(registration_data['date_of_birth'])
    return requests.post(
        'http://localhost:3000/users',
        json=registration_data,
        timeout=4,
    ).json()


@pytest.mark.django_db()
@httpretty.activate
def test_users_adding(
    client: Client,
    user_data: 'User',
    registration_data: 'RegistrationData',
    mock_server_users,
) -> None:
    """Check users adding."""
    httpretty.register_uri(
        httpretty.POST,
        'https://jsonplaceholder.typicode.com/users',
        body=json.dumps(mock_server_users, default=str),
    )

    response = client.post(
        reverse('identity:registration'),
        data=registration_data,
    )
    assert response.status_code == HTTPStatus.FOUND
