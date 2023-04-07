import pytest
import datetime as dt
from mimesis import Field, Schema
from mimesis.enums import Locale

from typing_extensions import TypeAlias
from server.apps.identity.models import User
from typing import Callable, Optional, TypedDict, final


@final
class RegData(TypedDict, total=False):
    """Represent the user data that is required to create a new user."""

    email: str
    first_name: str
    last_name: str
    date_of_birth: dt.datetime
    address: str
    job_title: str
    phone: str
    phone_type: int
    password: str
    password1: Optional[str]
    password2: Optional[str]


UserAssertion: TypeAlias = Callable[[RegData], None]
pytest_plugins = [
    'plugins.django_settings',
]


@pytest.fixture()
def user_data_factory():
    """Fabricate user data."""

    def factory(faker_seed, **fields) -> RegData:
        mf = Field(locale=Locale.RU, seed=faker_seed)
        password = mf('password')  # by default passwords are equal
        schema = Schema(schema=lambda: {
            'email': mf('person.email'),
            'first_name': mf('person.first_name'),
            'last_name': mf('person.last_name'),
            'date_of_birth': mf('datetime.date'),
            'address': mf('address.city'),
            'job_title': mf('person.occupation'),
            'phone': mf('person.telephone'),
        })
        return {
            **schema.create(iterations=1)[0],  # type: ignore[misc]
            **{'password': password},
            **fields,
        }

    return factory


@pytest.fixture()
def user_data(user_data_factory, faker_seed):
    """Random user data from factory."""
    return user_data_factory(faker_seed)


@pytest.fixture()
def registration_data(user_data: RegData) -> RegData:
    """User data with passwords for registration."""
    user_data['password1'] = user_data['password']
    user_data['password2'] = user_data['password']

    return user_data


@pytest.fixture(scope='session')
def assert_correct_user() -> UserAssertion:
    """Check that user created correctly."""

    def factory(expected: RegData) -> None:
        user = User.objects.get(email=expected['email'])
        # Special fields:
        assert user.id
        assert user.is_active
        assert not user.is_superuser
        assert not user.is_staff
        # All other fields:
        for field_name, data_value in expected.items():
            if not field_name.startswith('password'):
                assert getattr(user, field_name) == data_value

    return factory


@pytest.fixture()
def db_user(user_data: 'RegData') -> 'RegData':  # type: ignore[misc]
    """Inserts User to db and deletes after test."""
    user = User.objects.create(**user_data)
    yield user_data
    user.delete()
