"""Service for processing document files (PDF, DOCX)."""
import io
from typing import Tuple, Optional
from fastapi import UploadFile
import PyPDF2
from docx import Document as DocxDocument


class DocumentProcessor:
    """Processes document files and extracts text."""
    
    @staticmethod
    async def extract_text_from_pdf(file: UploadFile) -> Tuple[str, dict]:
        """
        Extract text from PDF file.
        
        Returns:
            Tuple of (text, metadata) where metadata includes page count
        """
        try:
            content = await file.read()
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")
                except Exception as e:
                    # Continue processing other pages if one fails
                    error_msg = f"[Error extracting text from this page: {str(e)}]"
                    text_parts.append(f"--- Page {page_num} ---\n{error_msg}\n")
            
            full_text = "\n".join(text_parts)
            
            if not full_text.strip():
                raise ValueError("No text extracted from PDF. This might be a scanned/image-only PDF that requires OCR.")
            
            metadata = {
                "page_count": page_count,
                "file_type": "pdf"
            }
            
            return full_text, metadata
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    @staticmethod
    async def extract_text_from_docx(file: UploadFile) -> Tuple[str, dict]:
        """
        Extract text from DOCX file.
        
        Returns:
            Tuple of (text, metadata)
        """
        try:
            content = await file.read()
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            full_text = "\n".join(text_parts)
            metadata = {
                "file_type": "docx",
                "paragraph_count": len(text_parts)
            }
            
            return full_text, metadata
            
        except Exception as e:
            raise ValueError(f"Failed to process DOCX: {str(e)}")
    
    @staticmethod
    async def extract_text(file: UploadFile) -> Tuple[str, dict]:
        """
        Extract text from document file (PDF or DOCX).
        
        Args:
            file: UploadFile object
            
        Returns:
            Tuple of (text, metadata)
        """
        filename = file.filename.lower() if file.filename else ""
        
        if filename.endswith(".pdf"):
            return await DocumentProcessor.extract_text_from_pdf(file)
        elif filename.endswith(".docx") or filename.endswith(".doc"):
            return await DocumentProcessor.extract_text_from_docx(file)
        else:
            raise ValueError(f"Unsupported file type. Supported: PDF, DOCX")
    
    @staticmethod
    def chunk_text(text: str, max_chunk_size: int = 10000) -> list[str]:
        """
        Split text into chunks for LLM processing.
        
        Args:
            text: Full text to chunk
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Try to split on paragraph boundaries
        paragraphs = text.split("\n\n")
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

