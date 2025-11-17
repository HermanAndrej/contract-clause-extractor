"""Basic API tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_extractions_empty():
    """Test listing extractions when none exist."""
    response = client.get("/api/extractions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 0


def test_get_nonexistent_extraction():
    """Test getting a non-existent extraction."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/extractions/{fake_id}")
    assert response.status_code == 404


def test_extract_without_file():
    """Test extraction endpoint without file."""
    response = client.post("/api/extract")
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422]

