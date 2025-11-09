# FastAPI RAG MVC Project

Lightweight Retrieval-Augmented Generation (RAG) service built with FastAPI using an MVC-like layout:

- ingestion → embedding → vector retrieval → LLM generation
- Local Chroma-style vector store and simple CRUD for documents & conversations

## Quick start (Windows)

1. Create a root dir an put the repo's files in it (Optionally: name the root dir backend).
2. Create & activate venv (in the backend folder):
   - python -m venv .venv
   - .venv\Scripts\activate
3. Install requirements
   - pip install -r requirements.txt
4. Start dev server
   - uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## Project structure (key files and folders)

There are two separate feature branches available in this repo:

1. **`feat/rag-from-scratch`**  
   This branch implements the RAG pipeline almost entirely from scratch:

   - document chunking + metadata
   - vector store + embeddings
   - vector similarity search
   - context augmentation
   - final response generation

2. **`feat/rag-llamaindex`**  
   This branch uses the LlamaIndex framework to perform all of the above operations for you.

app/

- **init**.py
- main.py
- controllers/
  - rag_controller_v1.py | rag_controller_v2.py (based on the branch you are in).
  - conversation_controller.py
- core/
  - config.py
  - db.py
  - logger.py
  - security.py
- data/
  - articles/ (sample documents)
- models/
  - document_models.py
  - document_crud.py
  - conversation_models.py
  - conversation_crud.py
  - user_models.py / user_crud.py
- services/
  - embedding_service.py
  - retriever_service.py
  - rag_service.py
  - generator_service.py
- utils/
  - file_loader.py
  - text_utils.py
  - logger.py

Use controllers for HTTP endpoints, services for business logic, models for persistence/CRUD, utils for helpers.

## System architecture (conceptual)

Components:

- Client (web / API consumer)
- FastAPI API layer (app.main + controllers)
- Orchestrator services (rag_service) that coordinate:
  - File ingestion & preprocessing (file_loader, text_utils)
  - Embedding generation & Vector store (embedding_service)
  - Retrieval (retriever_service + local vector DB)
  - Prompt construction & LLM generation (generator_service)
- Persistence (models + db)
- Logging & config (core/logger, core/config)

Data flow (simplified):
Client → FastAPI Controller → RAG Service
→ Embedding Service & Vector DB (index/store)
→ Retriever Service → RAG Service → Generator Service → Controller → Client
Persisted metadata stored via models/CRUD; conversations saved to enable context | session history.

ASCII overview:
Client
↓
[FastAPI Controllers] (app/controllers)
↓
[RAG Orchestrator] (app/services/rag_service)
├─ Embedding (app/services/embedding_service) → Vector DB (local)
├─ Retriever (app/services/retriever_service)
└─ Generator (app/services/generator_service)
↓
[Models / DB] (app/models + app/core/db)

## Endpoints (where to look)

- app/controllers/rag_controller_v1.py — main RAG endpoints (query, ingest, status)
- app/controllers/conversation_controller.py — conversation flows / history

## Challenges & solutions

- Document fragmentation and long contexts
  - Solution: chunk documents with overlap, normalize text, store metadata per chunk.
- Embedding mismatch and vector drift
  - Solution: standardize embedding model/version; re-embed on major model changes;
- Hallucinations from LLM output
  - Solution: include retrieved evidence in prompt; use strict grounding prompts; Activate thinking mode.
- Latency on retrieval + generation
  - Solution: async calls to LLM, increase vector index efficiency using HNSW indexing algorithm.

## Notes & next steps

- Check app/core/config.py for environment variables (API keys, model choices).
- Enable streaming responses.
- Refactor into a micro-services architecture. Proposed service boundaries:

  1. **Chunking Service**  
     Splits documents into chunks and generates rich metadata to improve vector-index recall.

  2. **Embeddings Service**  
     Generates vector embeddings for chunks (computationally expensive step).

  3. **Vector Store Service (Chroma)**  
     Stores embeddings + chunk metadata and performs vector similarity search.

  4. **Generation Service**  
     Produces LLM responses given the retrieved context.

- Caching, Monitoring, Error Handling.

  **Caching** (helps avoid recomputing work for repeat queries)  
  Examples: Query cache, Embeddings cache, Vector-search cache, LLM-response cache.

  **Monitoring** (to understand system behaviour in production):

  - Response time — how fast do we answer questions?
  - Throughput — how many queries/second can we handle?
  - Error rate — % of failed requests
  - Retrieval quality — are the returned chunks relevant to the user query?
  - Embedding performance — how long does it take to generate vectors?
  - Chunking efficiency — are we chunking documents well?

  Define alerting thresholds. Example:

  - If response time > 2s → performance issue
  - If error rate > 5% → system problem

  **Error Handling** (assume components _will_ fail):

  - Vector DB might go down
  - LLM service may be unavailable
  - Network calls may timeout

  The system should degrade gracefully — not collapse.  
  Example: if vector DB fails → fall back to keyword search instead of returning a 500.

For code navigation, open controllers first to see REST surface, then follow into services for orchestration.
