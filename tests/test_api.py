"""API tests."""
import io

import pytest

from app.api import routes as api_routes
from app.repositories.extraction_repository import ExtractionRepository
from app.services.extraction_service import ExtractionService


@pytest.fixture
def stub_api_services(dummy_document_processor, dummy_llm_service):
    repo = ExtractionRepository()
    service = ExtractionService(
        document_processor=dummy_document_processor,
        llm_service=dummy_llm_service,
        repository=repo,
    )
    api_routes.repository = repo
    api_routes.extraction_service = service
    yield service
    # Restore to default instances after test
    api_routes.repository = ExtractionRepository()
    api_routes.extraction_service = ExtractionService()


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_extractions_empty(client):
    """Test listing extractions when none exist."""
    response = client.get("/api/extractions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 0


def test_get_nonexistent_extraction(client):
    """Test getting a non-existent extraction."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/extractions/{fake_id}")
    assert response.status_code == 404


def test_extract_without_file(client):
    """Test extraction endpoint without file."""
    response = client.post("/api/extract")
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422]


def test_extract_and_retrieve_success(client, stub_api_services):
    """Test successful extraction flow using stubbed services."""
    file_bytes = ("Sample contract text " * 50).encode()
    response = client.post(
        "/api/extract",
        files={"file": ("contract.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["metadata"]["total_clauses"] == 1
    document_id = data["document_id"]

    # Retrieve extraction by ID
    get_resp = client.get(f"/api/extractions/{document_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["document_id"] == document_id
    assert len(retrieved["clauses"]) == 1

