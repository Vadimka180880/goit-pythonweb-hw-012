import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_fastapi_limiter():
    with patch("fastapi_limiter.depends.RateLimiter.__call__", return_value=None):
        yield
