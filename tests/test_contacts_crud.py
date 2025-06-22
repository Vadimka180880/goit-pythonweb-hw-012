import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"

@pytest.fixture
def auth_headers():
    client.post("/auth/signup", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    login = client.post("/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_contacts_list_unauthorized():
    response = client.get("/contacts/")
    assert response.status_code == 401

def test_create_contact(auth_headers):
    data = {"name": "Test User", "email": "contact@example.com", "phone": "+380501234567"}
    response = client.post("/contacts/", json=data, headers=auth_headers)
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        assert response.json()["email"] == data["email"]

def test_get_contacts(auth_headers):
    response = client.get("/contacts/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_contact(auth_headers):
    data = {"name": "Update User", "email": "update@example.com", "phone": "+380501234568"}
    create = client.post("/contacts/", json=data, headers=auth_headers)
    if create.status_code == 201:
        contact_id = create.json()["id"]
        upd = client.put(f"/contacts/{contact_id}", json={"name": "Updated"}, headers=auth_headers)
        assert upd.status_code in (200, 422)
    upd = client.put("/contacts/999999", json={"name": "Nope"}, headers=auth_headers)
    assert upd.status_code in (404, 422)

def test_delete_contact(auth_headers):
    data = {"name": "Delete User", "email": "delete@example.com", "phone": "+380501234569"}
    create = client.post("/contacts/", json=data, headers=auth_headers)
    if create.status_code == 201:
        contact_id = create.json()["id"]
        delete = client.delete(f"/contacts/{contact_id}", headers=auth_headers)
        assert delete.status_code == 204
    delete = client.delete("/contacts/999999", headers=auth_headers)
    assert delete.status_code in (404, 422)

def test_create_duplicate_contact(auth_headers):
    data = {"name": "Dup User", "email": "dup@example.com", "phone": "+380501234570"}
    client.post("/contacts/", json=data, headers=auth_headers)
    response = client.post("/contacts/", json=data, headers=auth_headers)
    assert response.status_code == 409

def test_contacts_invalid_token():
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/contacts/", headers=headers)
    assert response.status_code == 401

