import pytest
from fastapi.testclient import TestClient
from fastapi import status
from src.app.main import app, auth_service

client = TestClient(app)

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "password": "testpassword",
        "first_name": "Test",
        "last_name": "User"
    }

def test_register_user(user_data):
    response = client.post(
        "/register",
        params=user_data
    )
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()
    assert user_data["username"] in auth_service.users

def test_register_existing_user(user_data):
    # Сначала регистрируем пользователя
    client.post("/register", params=user_data)
    # Пытаемся зарегистрировать его снова
    response = client.post("/register", params=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Пользователь уже существует"}

def test_login_user(user_data):
    # Сначала регистрируем пользователя
    client.post("/register", params=user_data)
    # Пытаемся авторизоваться
    response = client.post(
        "/login",
        data={"username": user_data["username"], "password": user_data["password"]}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_login_invalid_user():
    response = client.post("/login", data={"username": "invaliduser", "password": "wrongpassword"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Неправильное имя пользователя или пароль"}

def test_health_check():
    response = client.get("/healthz/ready")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}
