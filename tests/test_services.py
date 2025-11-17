"""Service-layer tests."""
import uuid

import pytest

from app.services.document_processor import DocumentProcessor


def test_chunk_text_small():
    """Test chunking small text."""
    processor = DocumentProcessor()
    text = "This is a small text that should not be chunked."
    chunks = processor.chunk_text(text, max_chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_large():
    """Test chunking large text."""
    processor = DocumentProcessor()
    # Create text larger than chunk size
    text = "Paragraph one.\n\n" * 1000  # Large text
    chunks = processor.chunk_text(text, max_chunk_size=100)
    assert len(chunks) > 1
    # Verify all chunks together contain original text
    combined = "\n\n".join(chunks)
    assert len(combined) >= len(text) * 0.9  # Allow some variation


@pytest.mark.asyncio
async def test_extraction_service_extracts_and_updates(extraction_service, sample_upload_file):
    repo = extraction_service.repository
    doc = repo.create_document(filename="contract.pdf", file_size=1234, document_id=str(uuid.uuid4()))

    result = await extraction_service.extract_clauses(sample_upload_file, doc.id)

    assert result["metadata"]["total_clauses"] == 1
    stored_doc = repo.get_document(doc.id)
    assert stored_doc.status == "completed"
    clauses = repo.get_clauses(doc.id)
    assert len(clauses) == 1


@pytest.mark.asyncio
async def test_extraction_service_handles_short_text(extraction_service, sample_upload_file):
    # Override processor to return short text to trigger validation
    extraction_service.document_processor.extract_text = lambda file: ("short", {"file_type": "pdf"})
    repo = extraction_service.repository
    doc = repo.create_document(filename="short.pdf", file_size=10, document_id=str(uuid.uuid4()))

    with pytest.raises(ValueError):
        await extraction_service.extract_clauses(sample_upload_file, doc.id)

    stored_doc = repo.get_document(doc.id)
    assert stored_doc.status == "failed"

