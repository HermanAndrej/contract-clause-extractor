"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Clause(BaseModel):
    """Represents a single legal clause."""
    clause_id: str = Field(..., description="Unique identifier for the clause")
    title: str = Field(..., description="Title or heading of the clause")
    content: str = Field(..., description="Full text content of the clause")
    clause_type: Optional[str] = Field(
        None, 
        description="Type of clause (e.g., termination, payment, confidentiality, liability)"
    )
    page_number: Optional[int] = Field(None, description="Page number where clause appears")
    start_position: Optional[int] = Field(None, description="Character position where clause starts")
    end_position: Optional[int] = Field(None, description="Character position where clause ends")
    
    class Config:
        json_schema_extra = {
            "example": {
                "clause_id": "clause_001",
                "title": "Termination Clause",
                "content": "Either party may terminate this agreement...",
                "clause_type": "termination",
                "page_number": 5,
                "start_position": 1234,
                "end_position": 1567
            }
        }


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""
    document_id: str = Field(..., description="Unique identifier for the document")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="When the document was uploaded")
    processed_at: datetime = Field(..., description="When the extraction was completed")
    total_clauses: int = Field(..., description="Total number of clauses extracted")
    processing_time_seconds: float = Field(..., description="Time taken to process in seconds")
    status: str = Field(..., description="Status of extraction: pending, processing, completed, failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "contract.pdf",
                "file_size": 245678,
                "uploaded_at": "2024-01-15T10:30:00Z",
                "processed_at": "2024-01-15T10:30:15Z",
                "total_clauses": 12,
                "processing_time_seconds": 15.3,
                "status": "completed"
            }
        }


class ExtractionResponse(BaseModel):
    """Response model for extraction results."""
    document_id: str
    metadata: ExtractionMetadata
    clauses: List[Clause]
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "filename": "contract.pdf",
                    "file_size": 245678,
                    "uploaded_at": "2024-01-15T10:30:00Z",
                    "processed_at": "2024-01-15T10:30:15Z",
                    "total_clauses": 12,
                    "processing_time_seconds": 15.3,
                    "status": "completed"
                },
                "clauses": []
            }
        }


class ExtractionListItem(BaseModel):
    """Simplified model for listing extractions."""
    document_id: str
    filename: str
    uploaded_at: datetime
    processed_at: Optional[datetime]
    total_clauses: int
    status: str


class PaginatedExtractions(BaseModel):
    """Paginated list of extractions."""
    items: List[ExtractionListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None

