# Palm Mind AI — Conversational RAG Backend

A modular backend that supports document ingestion, semantic retrieval, conversational question answering, and interview booking through REST APIs.

## Features

- **Document ingestion:** Upload PDF and TXT documents.
- **Configurable chunking:** Supports fixed-size and recursive text chunking.
- **Embeddings:** Generates text embeddings using Google's Gemini API.
- **Vector search:** Stores and retrieves document chunks using Qdrant.
- **Conversational RAG:** Retrieves relevant document context and generates answers with Gemini.
- **Conversation memory:** Uses Redis to preserve multi-turn chat history.
- **Interview booking:** Collects candidate details and saves bookings to SQLite.
- **Metadata persistence:** Stores document metadata in a SQL database.
- **REST API documentation:** Interactive Swagger UI provided by FastAPI.

## Architecture

```text
Client
  |
  v
FastAPI REST API
  |
  +--> Document Ingestion
  |      |
  |      +--> PDF/TXT Text Extraction
  |      +--> Text Chunking
  |      +--> Gemini Embeddings
  |      +--> Qdrant Vector Storage
  |      +--> SQL Document Metadata
  |
  +--> Conversational Chat
  |      |
  |      +--> Redis Conversation History
  |      +--> Gemini Query Embedding
  |      +--> Qdrant Similarity Search
  |      +--> Gemini Answer Generation
  |
  +--> Interview Booking
         |
         +--> Multi-turn Detail Collection
         +--> SQLite Booking Persistence
```

## Technology Stack

- Python
- FastAPI
- Google Gemini API
- Qdrant
- Redis
- SQLAlchemy
- SQLite
- PyPDF
- pytest

## Requirements

- Python 3.13 or a compatible Python version
- A Google Gemini API key
- A running Qdrant instance
- A running Redis instance

## Setup

Clone the repository and open its directory:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd palm-mind-rag-backend
```

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Environment Configuration

Create a local `.env` file in the project root. Do not commit this file.

Configure the following variables with your own credentials and service URLs:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
GEMINI_EMBEDDING_MODEL=your_supported_embedding_model

QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=documents

REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./palm_mind.db
```

Use the exact environment variable names expected by `app/core/config.py`. Model availability depends on your Google API account and should be verified before running the application.

Initialize the SQL tables:

```bash
python init_db.py
```

## Run the Application

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/documents/ingest` | Upload, chunk, embed, and store a document |
| POST | `/api/v1/chat` | Ask questions using conversational RAG |
| POST | `/api/v1/bookings` | Create an interview booking |
| GET | `/api/v1/bookings/{booking_id}` | Retrieve a booking by ID |
| GET | `/health` | Check application health |

Use Swagger UI to inspect request schemas and test each endpoint.

## Run Tests

```bash
python -m pytest tests -v
```

## Design Notes

- The application uses modular API routes, services, schemas, database models, and vector-store code.
- Document text chunks are stored in Qdrant, while document metadata and interview bookings are persisted in SQL.
- Redis stores chat history and temporary booking conversation state.
- API credentials are loaded from environment configuration and should not be committed to source control.

## Limitations and Future Improvements

- Add more integration tests for Qdrant, Redis, SQL persistence, and end-to-end API behavior.
- Improve natural-language date and time extraction and add explicit candidate confirmation before saving bookings.
- Add authentication, rate limiting, and production deployment configuration.
- Add monitoring, structured logging, and retry policies for external services.
- Consider a production SQL database and managed Redis/Qdrant deployments for scaling.

## Security

Never commit API keys, `.env` files, local databases containing personal information, or virtual environment directories. Rotate any credentials that have been exposed.
