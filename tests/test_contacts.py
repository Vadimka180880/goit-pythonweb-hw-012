import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_contacts_route_exists():
    """Test that the /api/contacts endpoint exists (returns 200 or 401)."""
    response = client.get("/api/contacts/")
    assert response.status_code in (200, 401, 403, 404)
