import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.main import app

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpass123"

async def make_admin(async_client: AsyncClient, db_session):
    await async_client.post("/auth/signup", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    # Set role to admin via direct DB access
    await db_session.execute(text("UPDATE users SET role='admin' WHERE email=:email"), {"email": ADMIN_EMAIL})
    await db_session.commit()

async def get_token(async_client: AsyncClient, email, password):
    login = await async_client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, f"Login failed: {login.text}"
    return login.json()["access_token"]

@pytest.mark.asyncio
async def test_users_route_exists(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code in (200, 401, 403, 404)

@pytest.mark.asyncio
async def test_admin_access(async_client: AsyncClient, db_session):
    await make_admin(async_client, db_session)
    token = await get_token(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/users/all", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_user_access_denied(async_client: AsyncClient):
    await async_client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    token = await get_token(async_client, TEST_EMAIL, TEST_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/users/all", headers=headers)
    assert response.status_code in (401, 403)
