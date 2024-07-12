import pytest
import jwt
from datetime import datetime, timedelta
from src.app.auth_service import User, AuthService, SECRET_KEY


@pytest.fixture
def auth_service():
    return AuthService()


@pytest.fixture
def existing_user(auth_service):
    username = "existing_user"
    password = "password123"
    token = auth_service.register(username, password)
    return username, password, token


def test_register_new_user(auth_service):
    token = auth_service.register("new_user", "new_password")
    assert token is not None
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    assert payload['username'] == "new_user"


def test_register_existing_user(auth_service, existing_user):
    username, password, _ = existing_user
    token = auth_service.register(username, password)
    assert token is None


def test_authenticate_user(auth_service, existing_user):
    username, password, _ = existing_user
    token = auth_service.authenticate(username, password)
    assert token is not None
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    assert payload['username'] == username


def test_authenticate_user_invalid_password(auth_service, existing_user):
    username, _, _ = existing_user
    token = auth_service.authenticate(username, "wrong_password")
    assert token is None


def test_authenticate_nonexistent_user(auth_service):
    token = auth_service.authenticate("nonexistent_user", "password")
    assert token is None


@pytest.mark.parametrize("username,password", [
    ("user1", "password1"),
    ("user2", "password2"),
    ("user3", "password3"),
])
def test_register_multiple_users(auth_service, username, password):
    token = auth_service.register(username, password)
    assert token is not None
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    assert payload['username'] == username
