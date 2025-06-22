import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"

def get_token():
    client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    login = client.post("/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    if login.status_code == 200:
        return login.json()["access_token"]
    return None

def test_users_me_unauthorized():
    """Test that /users/me returns 401 if not authorized."""
    response = client.get("/users/me")
    assert response.status_code == 401

def test_users_me_authorized_and_cache():
    """Test that /users/me returns user data and uses Redis cache."""
    token = get_token()
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    # First call (should hit DB and cache user)
    response1 = client.get("/users/me", headers=headers)
    assert response1.status_code == 200
    user1 = response1.json()
    # Second call (should hit Redis cache)
    response2 = client.get("/users/me", headers=headers)
    assert response2.status_code == 200
    user2 = response2.json()
    assert user1["email"] == user2["email"]
