"""Repository for database operations."""
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.database import Document, Clause, get_session_factory


class ExtractionRepository:
    """Repository for managing extraction data."""
    
    def get_session(self) -> Session:
        """Get database session."""
        return get_session_factory()()
    
    def create_document(
        self,
        filename: str,
        file_size: int,
        document_id: Optional[str] = None
    ) -> Document:
        """Create a new document record."""
        session = self.get_session()
        try:
            doc = Document(
                id=document_id or str(uuid.uuid4()),
                filename=filename,
                file_size=file_size,
                status="pending"
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc
        finally:
            session.close()
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        session = self.get_session()
        try:
            return session.query(Document).filter(Document.id == document_id).first()
        finally:
            session.close()
    
    def update_document_status(
        self,
        document_id: str,
        status: str,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None
    ) -> Optional[Document]:
        """Update document status."""
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = status
                doc.error_message = error_message
                if status == "completed" or status == "failed":
                    doc.processed_at = datetime.utcnow()
                if processing_time is not None:
                    doc.processing_time_seconds = processing_time
                session.commit()
                session.refresh(doc)
            return doc
        finally:
            session.close()
    
    def save_clauses(self, document_id: str, clauses: List[dict]) -> List[Clause]:
        """Save clauses for a document."""
        session = self.get_session()
        try:
            # Delete existing clauses
            session.query(Clause).filter(Clause.document_id == document_id).delete()
            
            # Create new clauses
            clause_objects = []
            for idx, clause_data in enumerate(clauses):
                clause = Clause(
                    document_id=document_id,
                    clause_id=clause_data.get("clause_id", f"clause_{idx}"),
                    title=clause_data.get("title", ""),
                    content=clause_data.get("content", ""),
                    clause_type=clause_data.get("clause_type"),
                    page_number=clause_data.get("page_number"),
                    start_position=clause_data.get("start_position"),
                    end_position=clause_data.get("end_position"),
                    order_index=idx
                )
                clause_objects.append(clause)
                session.add(clause)
            
            session.commit()
            for clause in clause_objects:
                session.refresh(clause)
            return clause_objects
        finally:
            session.close()
    
    def get_clauses(self, document_id: str) -> List[Clause]:
        """Get all clauses for a document."""
        session = self.get_session()
        try:
            return (
                session.query(Clause)
                .filter(Clause.document_id == document_id)
                .order_by(Clause.order_index)
                .all()
            )
        finally:
            session.close()
    
    def list_documents(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Document], int]:
        """List documents with pagination."""
        session = self.get_session()
        try:
            total = session.query(Document).count()
            offset = (page - 1) * page_size
            documents = (
                session.query(Document)
                .order_by(desc(Document.uploaded_at))
                .offset(offset)
                .limit(page_size)
                .all()
            )
            return documents, total
        finally:
            session.close()

    def get_clause_counts(self, document_ids: List[str]) -> dict:
        """Return clause counts for provided document IDs in a single query."""
        if not document_ids:
            return {}

        session = self.get_session()
        try:
            results = (
                session.query(Clause.document_id, func.count(Clause.id))
                .filter(Clause.document_id.in_(document_ids))
                .group_by(Clause.document_id)
                .all()
            )
            return {doc_id: count for doc_id, count in results}
        finally:
            session.close()

