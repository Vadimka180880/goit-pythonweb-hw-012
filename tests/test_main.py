import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_docs_available():
    """Test that the OpenAPI docs endpoint is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text
