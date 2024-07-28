import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.app.main import app

client = TestClient(app)


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


def test_register():
    response = client.post(
        "/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "token" in response.json()


def test_register_existing_user():
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    response = client.post(
        "/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}


def test_login():
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    response = client.post(
        "/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "token" in response.json()


def test_login_invalid_user():
    response = client.post(
        "/login", json={"username": "invaliduser", "password": "invalidpass"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid username or password"}


@pytest.mark.asyncio
async def test_verify_token(async_client):
    response = client.post(
        "/register", json={"username": "testuser", "password": "testpass"})
    token = response.json()["token"]

    response = await async_client.post("/verify", json={"token": token})
    assert response.status_code == 200
    assert response.json() == {"user": "testuser"}


@pytest.mark.asyncio
async def test_verify_invalid_token(async_client):
    response = await async_client.post("/verify", json={"token": "invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
