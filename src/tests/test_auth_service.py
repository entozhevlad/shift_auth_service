import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

@pytest.fixture
def user_data():
    return {'username': 'testuser', 'password': 'testpassword'}

def test_register(user_data):
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    assert "token" in response.json()

def test_register_existing_user(user_data):
    client.post("/register", json=user_data)  # First registration
    response = client.post("/register", json=user_data)  # Second registration
    assert response.status_code == 400
    assert response.json() == {"detail": "User already exists"}

def test_login(user_data):
    client.post("/register", json=user_data)  # Register user first
    response = client.post("/login", data=user_data)
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_user():
    response = client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid username or password"}
