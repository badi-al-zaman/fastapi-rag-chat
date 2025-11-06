# FastAPI RAG MVC Project

Lightweight Retrieval-Augmented Generation (RAG) service built with FastAPI using an MVC-like layout:
- ingestion → embedding → vector retrieval → LLM generation
- Local Chroma-style vector store and simple CRUD for documents & conversations

## Quick start (Windows)
1. Create & activate venv (in the backend folder):
   - python -m venv .venv
   - .venv\Scripts\activate
2. Install requirements
   - pip install -r requirements.txt
3. Start dev server
   - uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## Project structure (key files and folders)
app/
- __init__.py
- main.py
- controllers/
  - rag_controller_v1.py
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
  - Embedding generation (embedding_service)
  - Vector store / retrieval (retriever_service + local vector DB)
  - Prompt construction & LLM generation (generator_service)
- Persistence (models + db)
- Logging & config (core/logger, core/config)

Data flow (simplified):
Client → FastAPI Controller → RAG Service
  → Embedding Service → Vector DB (index/store)
  → Retriever Service → RAG Service → Generator Service → Controller → Client
Persisted metadata stored via models/CRUD; conversations saved to enable context.

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
  - Solution: include retrieved evidence in prompt; use strict grounding prompts;
- Latency on retrieval + generation
  - Solution: async calls to LLM, increase vector index efficiency.

## Notes & next steps
- Check app/core/config.py for environment variables (API keys, model choices).
- Enable streaming responses.

For code navigation, open controllers first to see REST surface, then follow into services for orchestration.
