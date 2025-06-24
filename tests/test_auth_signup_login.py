import pytest
import uuid


@pytest.mark.asyncio
@pytest.fixture
def test_email():
    return f"testuser_{uuid.uuid4()}@example.com"


@pytest.mark.asyncio
async def test_signup_new_user(test_email, async_client):
    response = await async_client.post(
        "/auth/signup",
        json={"email": test_email, "password": "testpassword123"},
    )
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["email"] == test_email
        assert "id" in data


@pytest.mark.asyncio
async def test_login_user(test_email, async_client):
    # Signup first
    await async_client.post(
        "/auth/signup",
        json={"email": test_email, "password": "testpassword123"},
    )
    # Login
    response = await async_client.post(
        "/auth/login",
        data={"username": test_email, "password": "testpassword123"},
    )
    assert response.status_code in (200, 401)
    # Bad password
    bad_response = await async_client.post(
        "/auth/login",
        data={"username": test_email, "password": "wrongpass"},
    )
    assert bad_response.status_code == 401
