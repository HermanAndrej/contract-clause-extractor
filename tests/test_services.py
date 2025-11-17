"""Basic service tests."""
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

