"""SQLAlchemy database models."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    """Document model for storing extraction metadata."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class Clause(Base):
    """Clause model for storing extracted clauses."""
    __tablename__ = "clauses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    clause_id = Column(String, nullable=False)  # LLM-generated identifier
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    clause_type = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)  # For maintaining clause order
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="clauses")
    
    # Indexes
    __table_args__ = (
        Index("idx_document_id", "document_id"),
        Index("idx_clause_type", "clause_type"),
    )
    
    def __repr__(self):
        return f"<Clause(id={self.id}, title={self.title}, type={self.clause_type})>"


def init_db():
    """Initialize database tables."""
    from app.config import settings
    from sqlalchemy import create_engine
    
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine

