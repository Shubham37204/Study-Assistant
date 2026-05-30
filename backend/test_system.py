# backend/test_system.py
"""
Run from backend/:  python test_system.py
Tests every component independently. Fix failures before starting uvicorn.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def _ok(label: str, detail: str = "") -> None:
    print(f"  ✓  {label}" + (f" — {detail}" if detail else ""))


def _fail(label: str, err: Exception) -> None:
    print(f"  ✗  {label}")
    print(f"     {type(err).__name__}: {err}")


# ── 1 ─────────────────────────────────────────────────────────────────────
def test_config() -> bool:
    print("\n[1] Config & Environment")
    try:
        from config import settings
        assert settings.groq_api_key, "GROQ_API_KEY missing"
        _ok("Settings loaded")
        _ok("GROQ_API_KEY present")
        print(f"       database_url = {settings.database_url[:40]}...")
        print(f"       qdrant_url   = {settings.qdrant_url}")
        print(f"       celery_eager = {settings.celery_always_eager}")
        return True
    except Exception as e:
        _fail("Config load", e)
        return False


# ── 2 ─────────────────────────────────────────────────────────────────────
def test_database() -> bool:
    print("\n[2] Database (PostgreSQL / SQLite)")
    try:
        from sqlalchemy import text
        from db.database import SessionLocal, create_tables
        create_tables()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        _ok("Database connected and tables created")
        return True
    except Exception as e:
        _fail("Database", e)
        return False


# ── 3 ─────────────────────────────────────────────────────────────────────
def test_groq() -> bool:
    print("\n[3] Groq LLM API")
    try:
        from providers.llm.groq_provider import GroqProvider
        llm = GroqProvider()
        response = llm.complete(
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            model="llama-3.1-8b-instant",
            max_tokens=10,
        )
        assert response.strip(), "Empty response from Groq"
        _ok("Groq API", f"response='{response.strip()}'")
        return True
    except Exception as e:
        _fail("Groq API", e)
        return False


# ── 4 ─────────────────────────────────────────────────────────────────────
def test_embedder() -> bool:
    print("\n[4] Sentence Transformers (BGE-small)")
    try:
        from providers.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
        embedder = SentenceTransformerEmbedder()
        vecs = embedder.embed_documents(["test sentence"])
        assert len(vecs) == 1
        assert len(vecs[0]) == 384
        _ok("Embedder", f"384-dim vector ✓")
        return True
    except Exception as e:
        _fail("Embedder", e)
        return False


# ── 5 ─────────────────────────────────────────────────────────────────────
def test_qdrant() -> bool:
    print("\n[5] Qdrant Vector Store")
    try:
        from providers.vectorstores.qdrant_vector_store import QdrantVectorStore
        store = QdrantVectorStore()
        _ok("Qdrant connected", f"collection='{store.collection}'")
        return True
    except Exception as e:
        _fail("Qdrant", e)
        print("     → Start Qdrant: run qdrant.exe  OR  use Qdrant Cloud (cloud.qdrant.io)")
        return False


# ── 6 ─────────────────────────────────────────────────────────────────────
def test_bm25() -> bool:
    print("\n[6] BM25 Keyword Store")
    try:
        from providers.keyword.bm25_store import BM25KeywordStore
        store = BM25KeywordStore()
        _ok("BM25 store loaded")
        return True
    except Exception as e:
        _fail("BM25", e)
        return False


# ── 7 ─────────────────────────────────────────────────────────────────────
def test_full_ingestion() -> bool:
    print("\n[7] Full Ingestion Pipeline (text file)")
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "Artificial intelligence is transforming software engineering. "
                "Machine learning models process large datasets to find patterns. "
                "Retrieval-augmented generation combines search with language models."
            )
            tmp = f.name

        from api.dependencies import build_ingestion_agent
        from db.database import SessionLocal

        db = SessionLocal()
        try:
            agent = build_ingestion_agent(db_session=db)
            result = agent.run(
                source=tmp,
                user_id="system_test_user",
                original_filename="system_test.txt",
            )
        finally:
            db.close()
            Path(tmp).unlink(missing_ok=True)

        assert result.status == "success", f"status={result.status}, errors={result.errors}"
        _ok("Ingestion", f"{result.total_chunks} chunks, summary present={bool(result.summary)}")
        return True
    except Exception as e:
        _fail("Ingestion pipeline", e)
        return False


# ── 8 ─────────────────────────────────────────────────────────────────────
def test_query_pipeline() -> bool:
    print("\n[8] Query Pipeline (RAG graph)")
    try:
        from api.dependencies import (
            get_embedder, get_keyword_store, get_llm,
            get_reranker, get_vector_store,
        )
        from graph.rag_graph import RAGGraph

        graph = RAGGraph(
            llm=get_llm(),
            embedder=get_embedder(),
            vector_store=get_vector_store(),
            keyword_store=get_keyword_store(),
            reranker=get_reranker(),
        )
        result = graph.query(
            user_id="system_test_user",
            query_text="What is machine learning?",
            document_ids=[],
        )
        assert "answer" in result
        _ok("Query pipeline", f"answer length={len(result['answer'])} chars")
        return True
    except Exception as e:
        _fail("Query pipeline", e)
        return False


# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Study Assistant — System Diagnostics")
    print("=" * 55)

    tests = [
        test_config,
        test_database,
        test_groq,
        test_embedder,
        test_qdrant,
        test_bm25,
        test_full_ingestion,
        test_query_pipeline,
    ]

    results = []
    for t in tests:
        try:
            results.append(t())
        except Exception as e:
            print(f"  ✗  Unexpected crash in {t.__name__}: {e}")
            results.append(False)

    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 55)
    print(f"  {passed}/{len(results)} passed   {failed} failed")
    if failed == 0:
        print("  All systems operational. Safe to start the server.")
    else:
        print("  Fix failing components before starting uvicorn.")
    print("=" * 55)

    sys.exit(0 if failed == 0 else 1)
    