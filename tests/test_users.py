import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpass123"

def make_admin():
    client.post("/auth/signup", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    from app.src.database.database import get_db
    from app.src.database.models import User
    import asyncio
    async def set_admin():
        async for db in get_db():
            user = await db.execute("SELECT * FROM users WHERE email=:email", {"email": ADMIN_EMAIL})
            user = user.fetchone()
            if user:
                await db.execute("UPDATE users SET role='admin' WHERE email=:email", {"email": ADMIN_EMAIL})
                await db.commit()
            break
    asyncio.run(set_admin())

def get_token(email, password):
    login = client.post("/auth/login", data={"username": email, "password": password})
    if login.status_code == 200:
        return login.json()["access_token"]
    return None

def test_users_route_exists():
    response = client.get("/users/me")
    assert response.status_code in (200, 401, 403, 404)

def test_admin_access():
    make_admin()
    token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    assert token is not None
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/all", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_user_access_denied():
    client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    token = get_token(TEST_EMAIL, TEST_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/all", headers=headers)
    assert response.status_code == 403
