import os
import uuid
import asyncio
from unittest.mock import patch
from sqlalchemy.engine.url import make_url
from app.src.database.models import Base
from app.src.database.base import engine

# Patch Redis token functions BEFORE importing app/main
import app.src.services.auth as auth_mod
_token_store = {}
async def fake_store_refresh_token(jti, email, expires_in=604800):
    _token_store[jti] = email
async def fake_revoke_refresh_token(jti):
    _token_store.pop(jti, None)
async def fake_is_refresh_token_active(jti):
    return jti in _token_store
patch.object(auth_mod, "store_refresh_token", new=fake_store_refresh_token).start()
patch.object(auth_mod, "revoke_refresh_token", new=fake_revoke_refresh_token).start()
patch.object(auth_mod, "is_refresh_token_active", new=fake_is_refresh_token_active).start()

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from httpx import AsyncClient
from app.src.database.database import async_session

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_fastapi_limiter():
    with patch("fastapi_limiter.depends.RateLimiter.__call__", return_value=None):
        yield

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def user():
    # Generate a unique email for each test
    email = f"testuser_{uuid.uuid4().hex}@example.com"
    password = "string"
    client.post("/auth/signup", json={"email": email, "password": password, "role": "user"})
    class User:
        pass
    u = User()
    u.email = email
    u.password = password
    return u

@pytest_asyncio.fixture
async def db_session():
    async with async_session() as session:
        yield session

@pytest.fixture(scope="session", autouse=True)
def create_sqlite_tables():
    """
    Automatically create all tables in SQLite before running tests.
    Only runs if using SQLite (for local test mode).
    """
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):  # Only for SQLite
        async def _create():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.get_event_loop().run_until_complete(_create())
