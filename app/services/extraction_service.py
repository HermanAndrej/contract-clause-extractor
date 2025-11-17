"""Service that orchestrates document processing and clause extraction."""
import time
from typing import List, Dict
from fastapi import UploadFile
from app.services.document_processor import DocumentProcessor
from app.services.llm_service import LLMService
from app.repositories.extraction_repository import ExtractionRepository


class ExtractionService:
    """Orchestrates the extraction pipeline."""
    
    def __init__(
        self,
        document_processor: DocumentProcessor | None = None,
        llm_service: LLMService | None = None,
        repository: ExtractionRepository | None = None,
    ):
        """Initialize extraction service."""
        self.document_processor = document_processor or DocumentProcessor()
        self.llm_service = llm_service or LLMService()
        self.repository = repository or ExtractionRepository()
    
    async def extract_clauses(
        self,
        file: UploadFile,
        document_id: str
    ) -> Dict:
        """
        Extract clauses from a document file.
        
        Args:
            file: UploadFile object
            document_id: Document ID for tracking
            
        Returns:
            Dictionary with extraction results
        """
        start_time = time.time()
        
        try:
            # Update status to processing
            self.repository.update_document_status(document_id, "processing")
            
            # Extract text from document
            text, metadata = await self.document_processor.extract_text(file)
            
            if not text or len(text.strip()) < 100:
                raise ValueError(f"Document appears to be empty or too short ({len(text.strip())} chars)")
            
            # Chunk text if necessary (for large documents)
            max_chunk_size = 8000  # Leave room for prompt overhead
            chunks = self.document_processor.chunk_text(text, max_chunk_size)
            
            # Extract clauses using LLM
            if len(chunks) == 1:
                clauses = await self.llm_service.extract_clauses(text)
            else:
                clauses = await self.llm_service.extract_clauses_from_chunks(chunks)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save clauses to database
            self.repository.save_clauses(document_id, clauses)
            
            # Update document status
            self.repository.update_document_status(
                document_id,
                "completed",
                processing_time=processing_time
            )
            
            return {
                "clauses": clauses,
                "metadata": {
                    "total_clauses": len(clauses),
                    "processing_time_seconds": processing_time,
                    "chunks_processed": len(chunks),
                    "text_length": len(text)
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            # Update document status to failed
            self.repository.update_document_status(
                document_id,
                "failed",
                error_message=error_message,
                processing_time=processing_time
            )
            
            raise
    
    def get_extraction(self, document_id: str) -> Dict:
        """
        Get extraction results for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document and clauses
        """
        document = self.repository.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        clauses = self.repository.get_clauses(document_id)
        
        return {
            "document": document,
            "clauses": clauses
        }
    
    def list_extractions(self, page: int = 1, page_size: int = 10) -> Dict:
        """
        List all extractions with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Dictionary with paginated results
        """
        documents, total = self.repository.list_documents(page, page_size)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": documents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

