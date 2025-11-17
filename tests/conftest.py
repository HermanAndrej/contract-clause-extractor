"""Shared pytest fixtures for the Contract Clause Extractor."""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import database
from app.repositories.extraction_repository import ExtractionRepository
from app.services.document_processor import DocumentProcessor
from app.services.extraction_service import ExtractionService


TEST_DB_PATH = Path("./test_contracts.db").resolve()


@pytest.fixture(autouse=True)
def _reset_db():
    """Reset database to a temporary SQLite file for test isolation."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    database.reset_engine(f"sqlite:///{TEST_DB_PATH}")
    database.init_db()
    yield
    database.reset_engine()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class DummyDocumentProcessor:
    async def extract_text(self, file):
        return (
            "Sample contract text with sufficient content " * 5,
            {"file_type": "pdf", "page_count": 1},
        )

    def chunk_text(self, text: str, max_chunk_size: int = 10000):
        return DocumentProcessor.chunk_text(text, max_chunk_size)


class DummyLLMService:
    async def extract_clauses(self, text: str, is_chunk: bool = False):
        return [
            {
                "clause_id": "clause_001",
                "title": "Termination",
                "content": "Either party may terminate...",
                "clause_type": "termination",
                "page_number": 1,
                "start_position": 0,
                "end_position": 42,
            }
        ]

    async def extract_clauses_from_chunks(self, chunks):
        return [
            {
                "clause_id": f"chunk_{idx:03d}",
                "title": "Chunk",
                "content": chunk,
                "clause_type": "other",
                "page_number": None,
                "start_position": None,
                "end_position": None,
            }
            for idx, chunk in enumerate(chunks, 1)
        ]


@pytest.fixture
def dummy_document_processor():
    return DummyDocumentProcessor()


@pytest.fixture
def dummy_llm_service():
    return DummyLLMService()


@pytest.fixture
def extraction_service(dummy_document_processor, dummy_llm_service):
    repository = ExtractionRepository()
    return ExtractionService(
        document_processor=dummy_document_processor,
        llm_service=dummy_llm_service,
        repository=repository,
    )


@pytest.fixture
def sample_upload_file():
    class _UploadFile:
        def __init__(self, content: str, filename: str = "contract.pdf"):
            self._data = content.encode()
            self.filename = filename
            self.file = io.BytesIO(self._data)

        async def read(self):
            return self._data

    return _UploadFile("Sample contract text with sufficient length " * 10)
