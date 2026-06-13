# Chat With Your Docs

Upload a PDF, DOCX, or TXT file and ask questions about it. Answers come with source citations (filename, page, relevance score) so you can verify what the model is actually drawing from.

The goal was to produce something well-engineered and clearly reasoned, not just working.

![Screenshot placeholder](docs/screenshot.png)

---

## 1. Quick Start

You need Docker, an Anthropic API key, and an OpenAI API key.

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
docker-compose up --build
```

- App: http://localhost:3000
- API docs (Swagger UI): http://localhost:8000/docs

**Running without Docker** (faster iteration during development):

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

---

## 2. Architecture

Two separate flows: ingestion (upload time) and query (chat time).

### Ingestion flow

```
┌──────────┐   POST /api/documents/upload   ┌───────────────────┐
│  Browser │ ───────────────────────────────▶│  FastAPI           │
└──────────┘                                  │  (documents.py)   │
                                               └────────┬──────────┘
                                                        │ RAGPipeline.ingest()
                                                        ▼
                             ┌──────────────────────────────────────────────┐
                             │ DocumentProcessor                              │
                             │  PDF  → PyMuPDF, page-by-page                 │
                             │  DOCX → python-docx, paragraphs               │
                             │  TXT  → plain read                            │
                             │  → [{ text, metadata{filename,page,chunk} }]  │
                             └──────────────────────┬─────────────────────────┘
                                                     ▼
                             ┌──────────────────────────────────────────────┐
                             │ TextChunker                                    │
                             │  Recursive split: \n\n → \n → ". " → " " → ""│
                             │  CHUNK_SIZE=800, CHUNK_OVERLAP=150             │
                             └──────────────────────┬─────────────────────────┘
                                                     ▼
                             ┌──────────────────────────────────────────────┐
                             │ Embedder  (OpenAI text-embedding-3-small)     │
                             │  batched ≤100/req, retried with backoff       │
                             └──────────────────────┬─────────────────────────┘
                                                     ▼
                             ┌──────────────────────────────────────────────┐
                             │ VectorStore  (ChromaDB, ./chroma_data)        │
                             │  collection "documents", cosine distance      │
                             └──────────────────────────────────────────────┘
```

### Query flow

```
┌──────────┐   POST /api/chat    ┌───────────────────┐
│  Browser │ ───────────────────▶│  FastAPI           │
└──────────┘◀─────────────────── │  (chat.py)         │
   answer + sources + tokens      └────────┬──────────┘
                                            │ RAGPipeline.query()
                                            ▼
                         ┌──────────────────────────────────┐
                         │ Embedder.embed([question])        │
                         └─────────────────┬────────────────┘
                                            ▼
                         ┌──────────────────────────────────┐
                         │ VectorStore.search()              │
                         │  top-K=5, score_threshold=0.3     │
                         └─────────────────┬────────────────┘
                                            ▼
                         ┌──────────────────────────────────┐
                         │ Prompt assembly                   │
                         │  system prompt (grounding rules)  │
                         │  + retrieved chunks w/ sources    │
                         │  + last 5 conversation exchanges  │
                         │  + question                       │
                         └─────────────────┬────────────────┘
                                            ▼
                         ┌──────────────────────────────────┐
                         │ Claude  (claude-haiku-4-5-...)    │
                         └─────────────────┬────────────────┘
                                            ▼
                           { answer, sources[], tokens_used }
```

The query flow is also where the cost model makes sense: Claude only ever sees 5 chunks regardless of how large the original document was. A 1000-page PDF costs the same per query as a 10-page one once it's ingested.

---

## 3. Productionizing & Deploying on a Hyper-Scaler

The code structure is production-ready; the infrastructure isn't. Here's what it would take.

### Infrastructure changes

- **Auth**: JWT/OAuth2 with per-user document isolation. Right now any user sees all documents, that's fine for a prototype, unusable in production.
- **Async ingestion**: the upload endpoint currently blocks for the full ingestion duration. Large PDFs need a Celery + Redis (or SQS-backed) worker queue so the upload returns immediately with a `processing` status and the frontend polls for completion.
- **Cloud storage**: uploaded files are written to a temp path and deleted after ingestion. Production needs S3/GCS/Azure Blob to persist originals for re-processing or audit.
- **Production vector DB**: swap ChromaDB for Qdrant or pgvector, see the vector DB section below for reasoning.
- **Secrets management**: API keys injected from a secrets manager (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault) rather than `.env` files.
- **CI/CD**: GitHub Actions running lint, pytest, and `npm run build` on every PR; build & push Docker images to a registry on merge.

### AWS

ECS Fargate + ECR for both containers, ALB with path-based routing (`/api/*` → backend, `/*` → frontend) and TLS via ACM. S3 for document storage, RDS Postgres for document metadata and ingestion status, ElastiCache Redis for the Celery broker. Secrets Manager for API keys, CloudWatch with the `awslogs` driver for container logs, custom metrics for latency and token spend.

### GCP

Cloud Run handles both services with minimal ops overhead, it scales to zero, which is useful if usage is bursty. GCS replaces S3, Cloud SQL (Postgres) for metadata, Cloud Tasks or Pub/Sub for the async ingestion queue. Vertex AI has its own embedding models that could replace OpenAI if you want to stay within a single provider.

### Azure

Container Apps (serverless containers, similar to Cloud Run) for both services. Azure Blob Storage, Azure Database for PostgreSQL, Service Bus for the queue. Azure OpenAI Service is worth considering, it gives the same OpenAI models under Azure's compliance and networking controls, which matters in regulated industries.

### Cloudflare

A different pattern: Workers for the API layer, Vectorize as the vector store (purpose-built, globally distributed), R2 for document storage, and AI Gateway for request logging and rate limiting across LLM calls. This makes the most sense if low latency at the edge is a priority, the other three are more conventional containerized deployments.

---

## 4. RAG & LLM Decisions

### LLM: Claude (Anthropic)

`claude-haiku-4-5` for this prototype, fast and cheap enough to iterate on without watching token spend. In production I'd move to Sonnet for more complex documents where the reasoning quality difference matters. The main reason I chose Claude over GPT-4o is the larger context window and what I've found to be better instruction-following for the "answer only from context" constraint, less tendency to drift toward parametric knowledge when the retrieved context is sparse.

### Embedding model: `text-embedding-3-small`

The `-large` variant costs 5x more and stores 3x more dimensions with marginal recall improvement for general document Q&A. For a prototype with single-node ChromaDB, `text-embedding-3-small`'s 1536 dimensions are more than adequate. If I needed more precision, I'd consider Voyage AI (Anthropic's recommended embedding partner) before jumping to `-large`, their models are optimized specifically for retrieval.

### Vector store: ChromaDB now, Qdrant in production

ChromaDB with local file persistence is the right call for this scope: zero infrastructure, resets with `rm -rf chroma_data`, no external service. The reason it doesn't scale to production is that each replica would have its own on-disk index with no shared state, you can't run two backend instances. For production I'd re-implement the same `VectorStore` interface (`add_documents`, `search`, `delete_document`, `list_documents`) against Qdrant (horizontally scalable, built for this) or pgvector if there's already a Postgres instance and minimizing moving parts is the priority.

### Orchestration framework: none (built directly)

I considered LangChain and LlamaIndex. Both would have given me document loaders, a text splitter, and a retrieval chain out of the box. I chose not to use either because for a focused RAG pipeline, the abstractions add more weight than they save, LangChain in particular tends to obscure what's actually happening in the chunking and retrieval steps, which are the parts I wanted full visibility into. The whole pipeline is about 300 lines across four files (`document_processor.py`, `chunker.py`, `embedder.py`, `vector_store.py`, orchestrated by `rag_pipeline.py`), which felt more maintainable than threading LangChain primitives through the codebase. If the scope grew to multi-step agents or tool use, I'd revisit LlamaIndex.

### Prompt design & guardrails

The system prompt in `rag_pipeline.py` enforces three things:

1. **Closed-book grounding**: the model is explicitly told to answer only from the provided context, not from parametric knowledge. This is the main lever against hallucination, it doesn't eliminate it, but it significantly reduces drift.
2. **Explicit refusal**: when no chunks pass `score_threshold=0.3`, the context block says *(No relevant context was found)* and the system prompt instructs a specific fallback phrase. Testing with out-of-domain questions (e.g. asking about GPT-4 in a paper that predates it) confirmed this works, score drops to ~50% and the model declines cleanly rather than guessing.
3. **Mandatory citations**: enforced both in the prompt and in the structured `sources` array returned by `/api/chat`, so citations are verifiable independently of whatever prose the model generates.

Conversation history is capped at the last 5 exchanges to keep prompt size bounded. `max_tokens=1024` caps response length.

### Observability

Structured logging via structlog with JSON output in production. Every request gets a `request_id` (UUID) that propagates through all log entries for that request, useful for tracing a slow query across the embedding call, vector search, and LLM call. The RAG pipeline logs specific fields I care about: `retrieval_scores` (to spot degrading retrieval over time), `tokens_used` (cost monitoring), `chunk_count` (to catch documents that chunked unexpectedly), and `duration_ms` per component.

In production I'd add OpenTelemetry spans around each stage (embed → search → generate) to get distributed traces, and alert on: p95 latency > 5s, error rate > 1%, and average retrieval score dropping below 0.5 (which would suggest either the embeddings are degrading or users are asking questions the documents can't answer). LangSmith is also worth integrating for LLM-specific observability, prompt versioning, token cost per session, and answer quality tracking.

---

## 5. Key Technical Decisions

**FastAPI over Flask or Django**: native async matters here because every request involves I/O calls to OpenAI, Anthropic, and ChromaDB. Pydantic v2 models give free request validation and auto-generate the Swagger UI at `/docs`. Django would be overkill, no ORM, no admin, no forms.

**TypeScript on the frontend**: the types in `frontend/src/types/index.ts` mirror the backend's Pydantic models. It caught at least two shape mismatches during development that would have been silent runtime bugs in plain JS.

**Docker + docker-compose**: multi-stage builds keep images lean, and `docker-compose up` reproduces the full stack, including the persisted ChromaDB volume, in one command. The evaluator needs only Docker and two API keys.

---

## 6. Engineering Standards

**Applied**: clean layer separation (`DocumentProcessor` → `TextChunker` → `Embedder` → `VectorStore`, orchestrated by `RAGPipeline`), dependency injection for testability (collaborators are constructor args, FastAPI `Depends` wires the shared instance into endpoints), structured logging with `request_id` on every request, Pydantic v2 throughout, pinned dependencies, pytest unit tests with all external APIs mocked.

**Explicitly skipped**: auth/authorization, hybrid retrieval (BM25 + semantic), streaming responses, async ingestion queue, automated evaluation framework (RAGAS), CI/CD pipeline definitions. Not because they're unimportant, they're all in the "what I'd add" list, but because getting the core RAG behavior right was the priority.

---

## 7. AI Tools

I used Claude Code to scaffold the project from a detailed spec I wrote, covering file structure, module contracts, type signatures, and quality requirements. It generated the backend modules, frontend components, Docker setup, and test suite in one pass.

From there I reviewed every file before moving on. The parts I looked at most carefully: the chunker's splitting and merging logic (off-by-one errors are easy here), the cosine-distance-to-score conversion in `VectorStore.search`, the prompt template, and the metadata propagation (`filename`, `page_number`, `chunk_index`, `doc_id`) from ingestion through to the source citations. I ran the test suite locally to confirm the mocked behaviors matched the real ones.

The README and the reasoning in it are my own, the architecture decisions, the trade-off analysis, and the "what I'd do differently" reflect what I actually thought through while building this.

---

## 8. What I'd Do Differently

The thing that would most improve answer quality is **hybrid retrieval**, combining semantic search with BM25 keyword matching via Reciprocal Rank Fusion. Pure embedding similarity can miss exact matches on names, numbers, or model IDs where keyword search is more reliable. I noticed this during testing: asking for a specific numeric result retrieved the right page, but I'm not confident that holds for less common values.

After that, **re-ranking**: retrieve a broader top-20, run it through a cross-encoder (Cohere Rerank or a local `bge-reranker`), then pass only the top-5 to Claude. The first-stage retrieval optimizes for recall; re-ranking handles precision. The current setup conflates the two.

**Streaming responses** would meaningfully improve UX, right now the interface blocks for 2-3 seconds before showing anything. SSE to stream tokens as they arrive is straightforward with the Anthropic SDK.

Finally, a **RAGAS eval set** to measure faithfulness and answer relevancy objectively. Right now I'm evaluating by eye, which doesn't scale and misses regressions when chunking or prompting changes.