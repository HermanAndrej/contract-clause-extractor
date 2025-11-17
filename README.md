# Contract Clause Extractor

A FastAPI service that extracts and structures key clauses from legal contracts using LLM APIs.

## Overview

This service accepts contract documents (PDF, DOCX) via a REST API and uses OpenAI's GPT models to extract and structure legal clauses. Extracted clauses are stored in a SQLite database and can be retrieved via API endpoints.

## System Architecture

```
┌─────────────────┐
│   Client/API    │
│   Consumer      │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │   API Layer (Routes/Endpoints)    │  │
│  │   - POST /api/extract             │  │
│  │   - GET /api/extractions/{id}     │  │
│  │   - GET /api/extractions          │  │
│  └───────────┬───────────────────────┘  │
│              │                           │
│  ┌───────────▼───────────────────────┐  │
│  │   Service Layer                   │  │
│  │   - DocumentProcessor             │  │
│  │   - LLMService                    │  │
│  │   - ExtractionService             │  │
│  └───────────┬───────────────────────┘  │
│              │                           │
│  ┌───────────▼───────────────────────┐  │
│  │   Data Access Layer               │  │
│  │   - ExtractionRepository          │  │
│  └───────────┬───────────────────────┘  │
└──────────────┼───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│ Database │      │  LLM API    │
│ (SQLite) │      │  (OpenAI    │
│          │      │   GPT)      │
└──────────┘      └──────────────┘
```

### Component Flow

1. **API Layer**: FastAPI routes handle HTTP requests/responses with Pydantic validation
2. **Service Layer**: Business logic for document processing and extraction orchestration
3. **Document Processor**: Handles PDF/DOCX parsing and text extraction
4. **LLM Service**: Abstracts LLM API calls for clause extraction with prompt engineering
5. **Data Access Layer**: Repository pattern for database operations (CRUD)
6. **Database**: SQLite stores extraction results and metadata

## Features

- ✅ **PDF Processing**: Extract text from PDF documents
- ✅ **DOCX Processing**: Extract text from Word documents (bonus feature)
- ✅ **LLM-Powered Extraction**: Uses OpenAI GPT models (gpt-4o-mini by default) to identify and structure clauses
- ✅ **Structured Output**: Returns JSON with clause text, type, position, and metadata
- ✅ **Database Storage**: SQLite database for persistence
- ✅ **RESTful API**: FastAPI with automatic OpenAPI documentation
- ✅ **Docker Support**: Containerized for easy deployment

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional, for containerized deployment)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd contract-clause-extractor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Testing

- Create and activate a virtual environment (recommended to avoid globally installed pytest plugins interfering with the run)
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
  pip install -r requirements.txt
  ```
- Run the full suite (unit + API tests):
  ```bash
  pytest
  ```
- Tests rely on stubbed LLM/doc processors and a temporary SQLite file, so they pass without an OpenAI key.

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**
   ```bash
   docker build -t contract-extractor .
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here contract-extractor
   ```

## API Endpoints

### POST `/api/extract`

Extract clauses from a contract document.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: `file` (PDF or DOCX file)

**Response:**
```json
{
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
  "clauses": [
    {
      "clause_id": "clause_001",
      "title": "Termination",
      "content": "Either party may terminate this Agreement...",
      "clause_type": "termination",
      "page_number": 5,
      "start_position": 1234,
      "end_position": 1567
    }
  ]
}
```

### GET `/api/extractions/{document_id}`

Get extraction results for a specific document.

**Response:** Same structure as POST `/api/extract`

### GET `/api/extractions`

List all extractions with pagination.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 10, max: 100): Items per page

**Response:**
```json
{
  "items": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "contract.pdf",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:30:15Z",
      "total_clauses": 12,
      "status": "completed"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

## Demo Script

Run the end-to-end demo:

```bash
python demo.py
```

Make sure the server is running first. The script will:
1. Check server health
2. List existing extractions
3. Upload a test document (if available)
4. Extract clauses
5. Display results
6. Retrieve extraction by ID

## Project Structure

```
contract-clause-extractor/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration and settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic models
│   │   └── database.py         # SQLAlchemy models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py  # PDF/DOCX processing
│   │   ├── llm_service.py         # LLM integration
│   │   └── extraction_service.py  # Orchestration
│   └── repositories/
│       ├── __init__.py
│       └── extraction_repository.py  # Database operations
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── demo.py                     # E2E demo script
```

# Design Decisions & Technical Overview

---

## 🤖 LLM Provider: OpenAI GPT-4o-mini

* **Decision:** GPT-4o-mini (configurable; default).
* **Rationale:**
    * ✅ Cost-effective and fast.
    * ✅ Reliable and well-documented.
    * ✅ Excellent performance for structured clause extraction.
    * ✅ Supports `max_completion_tokens` for output control.
    * ❌ Slightly less accurate than GPT-4o for complex legal reasoning.
    * ❌ Shorter context window compared to other models like Claude.
* **Trade-off:** Prioritized **speed and cost** over maximum reasoning complexity. GPT-4o-mini delivers high-quality clause identification while remaining efficient and affordable. The LLM client is lazily instantiated, so swapping to another provider (e.g., Claude or a hosted fine-tuned model) is a single configuration change plus prompt adjustments.

---

## 🗃️ Database: SQLite

* **Decision:** SQLite for storage, with a clear migration path to PostgreSQL.
* **Rationale:**
    * ✅ Zero setup; lightweight and portable.
    * ✅ Easy to inspect and debug.
    * ✅ Fully sufficient for the demo/assignment scope.
    * ✅ Shared SQLAlchemy engine/session factory to avoid per-request engine churn.
    * ❌ Limited concurrency for high-volume production.
* **Trade-off:** Chose **simplicity and maintainability** over scalability. It's perfect for prototyping and can be easily upgraded later by pointing the shared engine helpers at PostgreSQL/Aurora.

---

## 📄 Document Processing: PyPDF2

* **Decision:** `PyPDF2` for PDF parsing.
* **Rationale:**
    * ✅ Lightweight and easy to use.
    * ✅ Fast and reliable for extracting text.
    * ❌ Limited table or complex layout extraction.
* **Trade-off:** Focused on **efficient text extraction**. Tables and advanced layouts are out of scope but could be handled in the future with tools like `pdfplumber`.

---

## 🏛️ Architecture: Service Layer Pattern

* **Decision:** Separation of API (FastAPI) and business logic via a dedicated service layer.
* **Rationale:**
    * ✅ Clear separation of concerns.
    * ✅ Makes logic testable and maintainable.
    * ✅ Easily extendable for new features (e.g., new document types).
    * ❌ Slightly more files and initial complexity.
* **Trade-off:** Chose **maintainability and code quality** over minimalism, which is crucial for building production-ready systems.

---

## ⚡ Concurrency: Async/Await

* **Decision:** Fully asynchronous I/O operations for all API endpoints.
* **Rationale:**
    * ✅ Optimized for LLM API calls and other I/O-bound operations.
    * ✅ Supports concurrent requests efficiently without blocking.
    * ❌ Slightly more complex code and stack traces.
* **Trade-off:** **Performance and scalability** take precedence. Async ensures a responsive, non-blocking API behavior, which is essential when waiting for external APIs like OpenAI.

---

## 🧩 Chunking Strategy

* **Decision:** Split large documents into manageable chunks for LLM processing.
* **Rationale:**
    * ✅ Handles token limits gracefully, preventing API errors.
    * ✅ Sequential processing ensures the integrity and order of results.
    * ❌ Slight loss of context between chunk boundaries.
    * ❌ Sequential processing is slower than parallel.
* **Trade-off:** **Functionality and reliability** were prioritized over raw speed. This can be optimized with parallel processing in a production environment.

---

## 🧠 Prompt Engineering Strategy

### Evolution

1.  **Initial Prompt:** A simple instruction to "extract clauses." This resulted in inconsistent JSON, missing clauses, and conversational text.
2.  **Iteration 1:** A structured prompt with a task description, a list of clause types, an example of the output, and explicit "JSON-only" instructions. This significantly improved consistency.
3.  **Iteration 2:** Added a `system` message to enforce the JSON-only role, provided a more detailed example, and used an explicit "RETURN ONLY JSON" instruction. This achieved reliable, machine-readable output.

### Final Approach

* **Role:** Defined the AI's role as a "Legal document analysis expert."
* **Instructions:**
    * Clear step-by-step instructions (Read, Identify, Format).
    * Provided a list of common clause types to look for.
    * Specified the exact output fields and JSON format (`clause_type`, `content`).
    * Explicit final instruction: "Return ONLY a valid JSON array."
* **Result:** This multi-step, role-based prompt produces high-quality, structured, and consistent JSON output. Chunked documents are processed sequentially to maintain the correct order of clauses, and the parser includes guardrails to recover from Markdown wrappers or malformed JSON.

---

## 🤖 AI Usage Documentation

### Key Contributions of AI (Gemini/ChatGPT)

* **Architecture & Design:** Explored and validated choices for the service layer pattern, database selection (SQLite vs. PostGres), and async strategies.
* **Prompt Engineering:** Iterated multiple times to develop a robust prompt that forces reliable JSON output from the LLM.
* **Error Handling:** Designed fallback parsing logic and structured error responses for the API.
* **Code Generation:** Assisted with FastAPI boilerplate, Pydantic data schemas, and SQLAlchemy database models.
* **Testing Strategy:** Helped define a test coverage plan, including edge cases (e.g., empty files, non-PDFs) and API workflows. The current suite covers API smoke tests plus an end-to-end happy path using stubbed services.

---

## 📝 Assumptions & Limitations

* **Input Format:** Assumes text-based PDFs or DOCX files. Scanned PDFs (images) are **not** supported.
* **Document Structure:** Performs best on documents with well-structured clauses (e.g., clear headings or distinct paragraphs).
* **Language:** Designed and tested for **English-language** documents.
* **File Size:** Configured for a maximum file size of **10MB**.
* **Chunking:** Handles ~8K characters per chunk (to fit GPT-4o-mini's context). Very large documents may require more advanced chunking logic or background processing.

---

## 🚀 Improvements with More Time

* **Testing:** Expand integration tests with live PDF fixtures and async test plugins; add load tests against the shared engine helpers.

* **Error Handling:** Add more granular error types, retry logic for failed API calls, and enhanced validation.

* **Performance:**
    * Implement **parallel processing** for document chunks or move extraction jobs to a queue.
    * Introduce caching (e.g., Redis) for LLM requests.
    * Move LLM processing to a background job (e.g., Celery) to make the API non-blocking.
    * Persist clause counts on the document to avoid aggregation queries when listing.

* **Features:**
    * Add **OCR support** (e.g., `pytesseract`) for scanned PDFs.
    * Implement clause **confidence scoring** from the LLM.
    * Add export formats (e.g., CSV, XLSX).
    * Build a search functionality for extracted clauses.

* **Production Readiness:**
    * Add authentication (e.g., OAuth2) and rate limiting.
    * Integrate structured monitoring and logging (e.g., Sentry, Grafana) plus better tracing of LLM calls.
    * Implement database migrations (e.g., Alembic) and multi-environment config for swapping SQLite -> PostgreSQL.

* **LLM Enhancements:**
    * Experiment with a fine-tuned legal model.
    * Implement smarter chunking (e.g., semantic chunking) to avoid cutting clauses in half.
    * Add a post-processing step to merge duplicate or fragmented clauses.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | Database connection string | `sqlite:///./contracts.db` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | Max tokens for LLM response | `2000` |
| `OPENAI_TEMPERATURE` | LLM temperature (lower = more consistent) | `0.1` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `10485760` (10MB) |
