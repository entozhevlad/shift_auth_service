import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from src.app.main import app


@pytest_asyncio.fixture
def user_data():
    return {
        "username": "testuser",
        "password": "testpassword",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client  # Здесь важно возвращать клиент через yield


@pytest.mark.asyncio
async def test_register_user(async_client, user_data):
    # Используем json вместо params
    response = await async_client.post("/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()


@pytest.mark.asyncio
async def test_register_existing_user(async_client, user_data):
    # Сначала регистрируем пользователя
    await async_client.post("/register", json=user_data)
    # Пытаемся зарегистрировать его снова
    response = await async_client.post("/register", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Пользователь уже существует"}


@pytest.mark.asyncio
async def test_login_user(async_client, user_data):
    # Сначала регистрируем пользователя
    await async_client.post("/register", json=user_data)
    # Пытаемся авторизоваться
    response = await async_client.post(
        "/login",
        data={"username": user_data["username"], "password": user_data["password"]}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid_user(async_client):
    response = await async_client.post(
        "/login",
        data={"username": "invaliduser", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Неправильное имя пользователя или пароль"}


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/healthz/ready")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}
