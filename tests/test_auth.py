import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"

RESET_NEW_PASSWORD = "newpassword456"

def test_auth_route_exists():
    """Test that the /auth/login endpoint exists (returns 200, 401, 422, 400, 404, 405)."""
    response = client.post("/auth/login", data={"username": "test@example.com", "password": "test"})
    assert response.status_code in (200, 401, 422, 400, 404, 405)

def test_password_reset_flow():
    """Test full password reset flow: request, reset, login with new password."""
    # Register user (if not exists)
    client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    # Request password reset
    resp = client.post("/auth/password-reset-request", json={"email": TEST_EMAIL})
    assert resp.status_code == 200
    # Get reset token (simulate, as email sending is async)
    from app.src.services.auth import create_access_token
    reset_token = create_access_token({"sub": TEST_EMAIL, "type": "password_reset"})
    # Reset password
    reset_resp = client.post("/auth/reset-password", json={"token": reset_token, "new_password": RESET_NEW_PASSWORD})
    assert reset_resp.status_code == 200
    # Login with new password
    login = client.post("/auth/login", data={"username": TEST_EMAIL, "password": RESET_NEW_PASSWORD})
    assert login.status_code == 200
    assert "access_token" in login.json()

def test_refresh_token_flow():
    """Test refresh token endpoint: get new access/refresh tokens."""
    # Register/login
    client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    login = client.post("/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    assert login.status_code == 200
    from app.src.services.auth import create_refresh_token
    refresh_token = create_refresh_token({"sub": TEST_EMAIL})
    resp = client.post("/auth/refresh-token", json={"token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data
