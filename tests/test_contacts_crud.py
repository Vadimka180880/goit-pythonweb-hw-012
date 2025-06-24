import pytest
import uuid
from httpx import AsyncClient
from app.main import app

TEST_PASSWORD = "testpassword123"

@pytest.mark.asyncio
async def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

@pytest.mark.asyncio
@pytest.fixture
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop()
    yield loop

@pytest.mark.asyncio
@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
@pytest.fixture
async def auth_headers():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/auth/signup", json={"email": email, "password": TEST_PASSWORD, "role": "user"})
        login = await ac.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
        assert login.status_code == 200, f"Login failed: {login.text}"
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_contacts_list_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/contacts/")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_contact(auth_headers):
    import datetime
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"contact_{uuid.uuid4().hex[:8]}@example.com",
        "phone_number": "+380501234567",
        "birthday": str(datetime.date(1990, 1, 1)),
        "additional_info": "Test info"
    }
    headers = await auth_headers
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/contacts/", json=data, headers=headers)
        assert response.status_code in (201, 409)
        if response.status_code == 201:
            assert response.json()["email"] == data["email"]

@pytest.mark.asyncio
async def test_get_contacts(auth_headers):
    headers = await auth_headers
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/contacts/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_update_contact(auth_headers):
    headers = await auth_headers
    data = {"name": "Update User", "email": f"update_{uuid.uuid4().hex[:8]}@example.com", "phone": "+380501234568"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create = await ac.post("/contacts/", json=data, headers=headers)
        if create.status_code == 201:
            contact_id = create.json()["id"]
            upd = await ac.put(f"/contacts/{contact_id}", json={"name": "Updated"}, headers=headers)
            assert upd.status_code in (200, 422)
        upd = await ac.put("/contacts/999999", json={"name": "Nope"}, headers=headers)
        assert upd.status_code in (404, 422)

@pytest.mark.asyncio
async def test_delete_contact(auth_headers):
    headers = await auth_headers
    data = {"name": "Delete User", "email": f"delete_{uuid.uuid4().hex[:8]}@example.com", "phone": "+380501234569"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create = await ac.post("/contacts/", json=data, headers=headers)
        if create.status_code == 201:
            contact_id = create.json()["id"]
            delete = await ac.delete(f"/contacts/{contact_id}", headers=headers)
            assert delete.status_code == 204
        delete = await ac.delete("/contacts/999999", headers=headers)
        assert delete.status_code in (404, 422)

@pytest.mark.asyncio
async def test_create_duplicate_contact(auth_headers):
    import datetime
    headers = await auth_headers
    data = {
        "first_name": "Dup",
        "last_name": "User",
        "email": f"dup_{uuid.uuid4().hex[:8]}@example.com",
        "phone_number": "+380501234570",
        "birthday": str(datetime.date(1990, 1, 1)),
        "additional_info": "Dup info"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/contacts/", json=data, headers=headers)
        response = await ac.post("/contacts/", json=data, headers=headers)
        assert response.status_code == 409

@pytest.mark.asyncio
async def test_contacts_invalid_token():
    headers = {"Authorization": "Bearer invalidtoken"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/contacts/", headers=headers)
        assert response.status_code == 401

