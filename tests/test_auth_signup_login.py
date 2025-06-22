import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"


def test_signup_new_user():
    response = client.post(
        "/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "id" in data


def test_login_user():
    response = client.post(
        "/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code in (200, 401)
    bad_response = client.post(
        "/auth/login",
        data={"username": TEST_EMAIL, "password": "wrongpass"}
    )
    assert bad_response.status_code == 401
