import pytest
import uuid
from httpx import AsyncClient
from app.main import app

TEST_PASSWORD = "testpassword123"

@pytest.mark.asyncio
async def get_token(email):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/auth/signup", json={"email": email, "password": TEST_PASSWORD})
        login = await ac.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
        if login.status_code == 200:
            return login.json()["access_token"]
        return None

@pytest.mark.asyncio
async def test_users_me_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/users/me")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_users_me_authorized_and_cache():
    email = f"testuser_{uuid.uuid4()}@example.com"
    token = await get_token(email)
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # First call (should hit DB and cache user)
        response1 = await ac.get("/users/me", headers=headers)
        assert response1.status_code == 200
        user1 = response1.json()
        # Second call (should hit Redis cache)
        response2 = await ac.get("/users/me", headers=headers)
        assert response2.status_code == 200
        user2 = response2.json()
        assert user1["email"] == user2["email"]
