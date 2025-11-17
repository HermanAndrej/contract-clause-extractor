"""API routes for the contract clause extractor."""
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from app.services.extraction_service import ExtractionService
from app.repositories.extraction_repository import ExtractionRepository
from app.models.schemas import (
    ExtractionResponse,
    ExtractionMetadata,
    Clause,
    ExtractionListItem,
    PaginatedExtractions,
    ErrorResponse
)
from app.config import settings
from datetime import datetime

router = APIRouter()

extraction_service = ExtractionService()
repository = ExtractionRepository()


@router.post("/extract", response_model=ExtractionResponse, status_code=201)
async def extract_clauses(file: UploadFile = File(...)):
    """
    Extract clauses from a contract document.
    
    Supports PDF and DOCX files.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Check file size (read and reset)
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    # Reset file pointer for processing
    file.file.seek(0)
    
    # Create document record
    document_id = str(uuid.uuid4())
    document = repository.create_document(
        filename=file.filename,
        file_size=file_size,
        document_id=document_id
    )
    
    try:
        # Extract clauses
        result = await extraction_service.extract_clauses(file, document_id)
        
        # Get updated document
        document = repository.get_document(document_id)
        clauses_data = result["clauses"]
        
        # Convert to response models
        clauses = [
            Clause(
                clause_id=c.get("clause_id", ""),
                title=c.get("title", ""),
                content=c.get("content", ""),
                clause_type=c.get("clause_type"),
                page_number=c.get("page_number"),
                start_position=c.get("start_position"),
                end_position=c.get("end_position")
            )
            for c in clauses_data
        ]
        
        metadata = ExtractionMetadata(
            document_id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at or datetime.utcnow(),
            total_clauses=len(clauses),
            processing_time_seconds=document.processing_time_seconds or 0.0,
            status=document.status
        )
        
        return ExtractionResponse(
            document_id=document.id,
            metadata=metadata,
            clauses=clauses
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/extractions/{document_id}", response_model=ExtractionResponse)
async def get_extraction(document_id: str):
    """
    Get extraction results for a specific document.
    """
    try:
        result = extraction_service.get_extraction(document_id)
        document = result["document"]
        clauses_orm = result["clauses"]
        
        # Convert ORM objects to Pydantic models
        clauses = [
            Clause(
                clause_id=c.clause_id,
                title=c.title,
                content=c.content,
                clause_type=c.clause_type,
                page_number=c.page_number,
                start_position=c.start_position,
                end_position=c.end_position
            )
            for c in clauses_orm
        ]
        
        metadata = ExtractionMetadata(
            document_id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at or datetime.utcnow(),
            total_clauses=len(clauses),
            processing_time_seconds=document.processing_time_seconds or 0.0,
            status=document.status
        )
        
        return ExtractionResponse(
            document_id=document.id,
            metadata=metadata,
            clauses=clauses
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/extractions", response_model=PaginatedExtractions)
async def list_extractions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    List all extractions with pagination.
    """
    try:
        result = extraction_service.list_extractions(page, page_size)
        document_ids = [doc.id for doc in result["items"]]
        clause_counts = repository.get_clause_counts(document_ids)
        
        items = [
            ExtractionListItem(
                document_id=doc.id,
                filename=doc.filename,
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
                total_clauses=clause_counts.get(doc.id, 0),
                status=doc.status
            )
            for doc in result["items"]
        ]
        
        return PaginatedExtractions(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

