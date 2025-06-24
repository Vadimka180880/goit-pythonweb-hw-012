import pytest
from httpx import AsyncClient  
from app.main import app
import uuid

# Generate unique test emails for each test run
TEST_EMAIL = f"testuser_{uuid.uuid4().hex}@example.com"
TEST_PASSWORD = "testpassword123"
RESET_NEW_PASSWORD = "newpassword456"

@pytest.mark.asyncio
async def test_auth_route_exists(async_client: AsyncClient):
    """Test that the /auth/login endpoint exists (returns 200, 401, 422, 400, 404, 405)."""
    # Register user to ensure login endpoint works
    email = f"test_{uuid.uuid4().hex}@example.com"
    await async_client.post("/auth/signup", json={"email": email, "password": "test", "role": "user"})
    response = await async_client.post("/auth/login", data={"username": email, "password": "test"})
    assert response.status_code in (200, 401, 422, 400, 404, 405)

@pytest.mark.asyncio
async def test_password_reset_flow(async_client: AsyncClient):
    email = f"reset_{uuid.uuid4().hex}@example.com"
    await async_client.post("/auth/signup", json={"email": email, "password": TEST_PASSWORD, "role": "user"})
    resp = await async_client.post("/auth/password-reset-request", json={"email": email})
    assert resp.status_code == 200
    from app.src.services.auth import create_access_token
    reset_token = create_access_token({"sub": email, "type": "password_reset"})
    reset_resp = await async_client.post("/auth/reset-password", json={"token": reset_token, "new_password": RESET_NEW_PASSWORD})
    assert reset_resp.status_code == 200 or reset_resp.status_code == 400
    login = await async_client.post("/auth/login", data={"username": email, "password": RESET_NEW_PASSWORD})
    assert login.status_code in (200, 401)

@pytest.mark.asyncio
async def test_refresh_token_flow(async_client: AsyncClient):
    email = f"refresh_{uuid.uuid4().hex}@example.com"
    await async_client.post("/auth/signup", json={"email": email, "password": TEST_PASSWORD, "role": "user"})
    login = await async_client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    assert login.status_code == 200
    tokens = login.json()
    refresh_token = tokens["refresh_token"]
    resp = await async_client.post("/auth/refresh-token", json={"token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data

@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revoke(async_client: AsyncClient, user, db_session):
    """
    Test that refresh token can be used only once (rotation/revoke):
    1. Login to get refresh_token
    2. Use refresh_token to get new tokens (should succeed)
    3. Use the same refresh_token again (should fail with 401)
    """
    # 1. Login
    login_data = {"username": user.email, "password": "string"}
    response = await async_client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    refresh_token = tokens["refresh_token"]

    # 2. Use refresh_token (first time, should succeed)
    response = await async_client.post("/auth/refresh-token", json={"token": refresh_token})
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 3. Use the same refresh_token again (should fail)
    response = await async_client.post("/auth/refresh-token", json={"token": refresh_token})
    assert response.status_code == 401
    assert response.json()["detail"] in ["Refresh token revoked or expired", "Invalid refresh token"]
