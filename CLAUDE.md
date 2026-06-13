# CLAUDE.md

Instructions for AI coding assistants (Claude Code and similar) working in this repository.

## Project Overview

"Chat With Your Docs" is a full-stack RAG application: users upload PDF/DOCX/TXT
documents, and a FastAPI backend chunks, embeds, and stores them in ChromaDB so a
React frontend can ask natural-language questions and receive Claude-generated
answers grounded in cited source passages.

## Tech Stack

- **Backend**: FastAPI (Python 3.11), Pydantic v2, structlog, uvicorn
- **LLM**: Anthropic Claude via the `anthropic` SDK (model configurable, default `claude-3-5-haiku-20241022`)
- **Embeddings**: OpenAI `text-embedding-3-small` via the `openai` SDK
- **Vector store**: ChromaDB with local persistence (`./chroma_data`)
- **Document processing**: PyMuPDF (PDF), `python-docx` (DOCX), plain text (TXT)
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS
- **Infra**: Docker + docker-compose (multi-stage builds)
- **Tests**: pytest (+ pytest-asyncio) with mocked external APIs

## Key Conventions

- All FastAPI endpoint handlers are `async def`.
- Request/response bodies are Pydantic v2 models (see `backend/app/models/`).
- Use `structlog` (`app.utils.logging.get_logger`) for all logging — never `print`.
  Every request is logged with a `request_id`, method, endpoint, and `duration_ms`.
- Type hints are required on every function signature, including return types.
- Every class and public method has a docstring.
- No bare `except:` — always catch specific exception types.
- Settings are loaded via `pydantic-settings` (`app.config.get_settings`, cached
  with `lru_cache`). Never read `os.environ` directly elsewhere.
- The `RAGPipeline` (constructed once in `app.main.lifespan`, stored on
  `app.state.rag_pipeline`) is the single entry point for ingestion and querying;
  endpoints should not call `DocumentProcessor`/`Embedder`/`VectorStore` directly.

## File Structure Notes

```
backend/app/
├── main.py              # FastAPI app, lifespan, CORS, request logging middleware
├── config.py            # Settings (pydantic-settings)
├── api/
│   ├── router.py        # Aggregates endpoint routers under /api
│   ├── dependencies.py   # get_pipeline() — shared RAGPipeline dependency
│   └── endpoints/        # documents, chat, health
├── core/
│   ├── document_processor.py  # PDF/DOCX/TXT -> text + metadata sections
│   ├── chunker.py              # Recursive character text splitter
│   ├── embedder.py             # OpenAI embeddings, batched + retried
│   ├── vector_store.py         # ChromaDB wrapper
│   └── rag_pipeline.py         # Orchestrates ingest() and query()
├── models/               # Pydantic request/response models
└── utils/logging.py      # structlog configuration

frontend/src/
├── components/   # DocumentUploader, DocumentList, ChatInterface, MessageBubble, SourceCitation
├── hooks/         # useDocuments, useChat
├── services/api.ts  # Typed fetch wrapper (VITE_API_URL)
└── types/index.ts   # Shared TS types mirroring backend Pydantic models
```

## Common Commands

### Backend (from `backend/`)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY / OPENAI_API_KEY

# Run the dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

### Frontend (from `frontend/`)

```bash
npm install
npm run dev      # Vite dev server on :5173
npm run build    # Type-check + production build
```

### Docker (from repo root)

```bash
cp .env.example .env   # then fill in API keys
docker-compose up --build
# backend:  http://localhost:8000
# frontend: http://localhost:3000
```
