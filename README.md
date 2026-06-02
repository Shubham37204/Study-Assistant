# Study Assistant

<div align="center">

**Upload your PDFs. Ask questions. Get cited answers grounded in your own notes.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_RAG-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Qdrant](https://img.shields.io/badge/Qdrant-Cloud-DC143C?style=flat-square)](https://qdrant.tech)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

[Live Demo](https://your-demo-url.vercel.app) · [Report Bug](https://github.com/Shubham37204/Study-Assistant/issues) · [Backend API Docs](https://your-api.railway.app/docs)

</div>

---

## Overview

Study Assistant is a production-grade AI system that lets you upload documents and ask natural-language questions about them. Every answer is grounded in retrieved evidence and comes with source citations — the system cannot hallucinate content that is not in your documents.

The backend implements a **multi-agent RAG pipeline** using LangGraph: a query understanding agent rewrites and classifies the intent, a planning agent chooses the retrieval strategy, a retrieval agent runs hybrid vector + keyword search with reranking, a generation agent produces a grounded answer using conversation history, and a critic agent verifies the answer is supported by evidence before it is returned.

---

## Demo

> Upload a PDF → select it → ask a question → receive a cited answer

![Study Assistant Demo](docs/demo.gif)

---

## Architecture

```
                        ┌──────────────────────────────────────────┐
                        │              LangGraph Pipeline           │
                        │                                          │
  User Query            │  Query Understanding                     │
      │                 │    ↓ intent + rewrite                    │
      ▼                 │  Planning Agent                          │
  FastAPI /query  ──►   │    ↓ search strategy + top_k            │
                        │  Retrieval Agent                         │
                        │    ├── Qdrant  (vector similarity)       │
                        │    ├── BM25    (keyword match)           │
                        │    ├── RRF     (score fusion)            │
                        │    └── Cross-Encoder (rerank)            │
                        │  Generation Agent (Groq LLaMA 70B)       │
                        │    ↓ answer + citations                  │
                        │  Critic Agent                            │
                        │    ↓ grounding check → retry up to 2×   │
                        │  Finalize                                │
                        └──────────────────────────────────────────┘
                                         │
                              Cited answer returned
```

```
                        ┌─────────────────────────────────────────┐
                        │           Ingestion Pipeline            │
                        │                                         │
  File Upload           │  FileDetector → Extractor              │
      │                 │    ├── PyMuPDF  (text PDFs)            │
      ▼                 │    ├── EasyOCR  (scanned PDFs)         │
  Celery Worker  ──►    │    ├── EasyOCR  (images)               │
  (async)               │    └── Trafilatura (URLs)              │
                        │  TextCleaner → Chunker                  │
                        │  Embedder (BGE-small-en)                │
                        │  Qdrant upsert + BM25 index             │
                        │  LLM Summarizer (Groq 8B)              │
                        │  PostgreSQL save                        │
                        └─────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI, Python 3.12, Uvicorn |
| **AI Orchestration** | LangGraph, LangChain |
| **LLM** | Groq (LLaMA 3.3 70B / LLaMA 3.1 8B) |
| **Embeddings** | sentence-transformers `BAAI/bge-small-en-v1.5` |
| **Vector Database** | Qdrant Cloud |
| **Keyword Search** | BM25 (rank-bm25) |
| **Reranking** | Cross-encoder `ms-marco-MiniLM-L-6-v2` |
| **Relational DB** | PostgreSQL via Supabase, SQLAlchemy 2.0 |
| **Task Queue** | Celery + Redis |
| **OCR** | EasyOCR, PyMuPDF |
| **Observability** | LangSmith tracing |
| **Frontend** | React 18, Vite, Tailwind CSS, shadcn/ui |
| **Auth** | Clerk (JWT) |
| **State Management** | Zustand (persist), TanStack Query v5 |
| **Deployment** | Vercel (frontend), Railway (backend) |

---

## Features

- **Multi-format ingestion** — PDFs (text and scanned), images, text files, markdown
- **OCR fallback** — scanned PDFs are automatically rendered and OCR-processed page by page
- **Hybrid retrieval** — vector similarity + BM25 keyword search fused with Reciprocal Rank Fusion
- **Cross-encoder reranking** — top candidates are reranked before generation
- **Grounded generation** — answers are verified against retrieved evidence; ungrounded answers trigger a retry
- **Source citations** — every answer references the exact chunk it was derived from
- **Scoped conversation history** — each document selection has its own independent chat history
- **Async ingestion** — uploads return immediately; processing runs in a Celery worker with job polling
- **Per-user isolation** — all vector, keyword, and database queries are scoped by authenticated user ID
- **Intent classification** — queries are classified as factual, summarize, explain, or compare
- **LangSmith tracing** — full LLM call visibility for debugging and latency monitoring

---

## Project Structure

```
study-assistant/
│
├── backend/
│   ├── agents/                 # LangGraph agent nodes
│   │   ├── query_agent.py      # intent classification, query rewrite
│   │   ├── planning_agent.py   # search strategy selection
│   │   ├── retrieval_agent.py  # hybrid search orchestration
│   │   ├── generation_agent.py # grounded answer generation
│   │   ├── critic_agent.py     # grounding verification
│   │   └── ingestion_agent.py  # document processing pipeline
│   │
│   ├── api/
│   │   ├── main.py             # FastAPI app, CORS, lifespan
│   │   ├── dependencies.py     # provider injection, singleton factories
│   │   └── routes/
│   │       ├── upload.py       # POST /upload
│   │       ├── query.py        # POST /query
│   │       ├── documents.py    # GET/DELETE /documents
│   │       └── jobs.py         # GET /jobs/{job_id}
│   │
│   ├── core/
│   │   ├── chunker.py          # text chunking with overlap
│   │   ├── hybrid_search.py    # RRF score fusion
│   │   ├── reranker.py         # cross-encoder reranking
│   │   ├── cache.py            # Redis query cache
│   │   ├── summarizer.py       # document summarization
│   │   ├── text_cleaner.py     # text normalization
│   │   ├── file_detector.py    # file type detection
│   │   └── extractors/         # PDF, image, text, URL extractors
│   │
│   ├── db/
│   │   ├── models.py           # SQLAlchemy Document + Page models
│   │   ├── repository.py       # DB access layer
│   │   └── database.py         # engine, session factory
│   │
│   ├── graph/
│   │   └── rag_graph.py        # LangGraph pipeline definition
│   │
│   ├── middleware/
│   │   └── clerk_auth.py       # Clerk JWT verification
│   │
│   ├── providers/              # abstract provider interfaces
│   │   ├── llm/                # Groq LLM provider
│   │   ├── embeddings/         # sentence-transformers embedder
│   │   ├── vectorstores/       # Qdrant vector store
│   │   └── keyword/            # BM25 keyword store
│   │
│   ├── schemas/                # Pydantic models (API, ingestion, graph)
│   ├── tasks/                  # Celery ingestion task
│   ├── config.py               # pydantic-settings configuration
│   ├── celery_app.py           # Celery application factory
│   └── test_comprehensive.py   # 94-test suite with mocked providers
│
└── frontend/
    └── src/
        ├── api/                # Axios client, documents, query
        ├── components/
        │   ├── chat/           # ChatWindow, MessageBubble, CitationCard
        │   ├── documents/      # DocumentList, DocumentItem, UploadZone
        │   ├── layout/         # Header, Sidebar, Footer, MainLayout
        │   └── ui/             # shadcn components, EmptyState, ErrorBoundary
        ├── hooks/              # useUpload, useQuery, useDocuments, useDeleteDocument
        ├── pages/              # AuthPage, DashboardPage
        └── store/              # Zustand store with scoped conversations
```

---

## Local Setup

### Prerequisites

- Python 3.12
- Node.js 18+
- A running Redis instance (or skip with `CELERY_ALWAYS_EAGER=true`)
- [Qdrant Cloud](https://cloud.qdrant.io) cluster
- [Supabase](https://supabase.com) project (PostgreSQL)
- [Groq](https://console.groq.com) API key
- [Clerk](https://clerk.com) application
- [LangSmith](https://smith.langchain.com) project (optional, for tracing)

### 1. Clone

```bash
git clone https://github.com/Shubham37204/Study-Assistant.git
cd Study-Assistant
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
# add VITE_CLERK_PUBLISHABLE_KEY
npm run dev
```

Open `http://localhost:5173`

---

## Environment Variables

### `backend/.env`

```env
# LLM
GROQ_API_KEY=gsk_...

# Auth
CLERK_SECRET_KEY=sk_test_...

# Database
DATABASE_URL=postgresql://postgres:...@...supabase.com:5432/postgres

# Vector Store
QDRANT_URL=https://....aws.cloud.qdrant.io
QDRANT_API_KEY=...
QDRANT_COLLECTION=study_assistant
EMBED_SIZE=384

# Cache / Queue
REDIS_URL=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=true          # set false in production

# Observability (optional)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=study-assistant
```

### `frontend/.env`

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_API_BASE_URL=                # leave empty for dev (Vite proxy)
```

---

## Running Tests

```bash
cd backend
python -m pytest test_comprehensive.py -v
```

The test suite covers 94 cases across:

- Configuration loading and validation
- Database CRUD — save, get, list, delete, field mapping
- File detection for all supported types
- Text, unicode, and empty file extraction
- Query cache key generation and Redis failure handling
- Groq LLM provider — success, rate limit, empty response
- Clerk auth middleware — no credentials, invalid token, missing JWKS
- Upload route — valid file, unsupported extension, size limit, empty file
- Query route — cache hit, missing fields, conversation history, empty query
- Documents route — list, delete, ownership check, field mapping verification
- Jobs route — pending, success, failed, processing states
- Health endpoint — Redis up/down status
- Qdrant vector store — filter building, exception handling, dimension mismatch
- Ingestion agent — full pipeline, unsupported type, filename preservation
- RAG graph — normal query, document scope, conversation history, empty retrieval

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload and ingest a document |
| `GET` | `/jobs/{job_id}` | Poll async ingestion job status |
| `GET` | `/documents` | List user's documents |
| `DELETE` | `/documents/{id}` | Delete document and all its vectors |
| `POST` | `/query` | Run RAG query against selected documents |
| `GET` | `/health` | Backend health + Redis status |

Full interactive docs available at `/docs` when the backend is running.

