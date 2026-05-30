# backend/test_system.py — updated with query test
"""
Run from backend/: python test_system.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path


def _ok(label, detail=""):
    print(f"  ✓  {label}" + (f" — {detail}" if detail else ""))


def _fail(label, err):
    print(f"  ✗  {label}")
    print(f"     {type(err).__name__}: {err}")


def test_config():
    print("\n[1] Config")
    try:
        from config import settings
        assert settings.groq_api_key
        _ok("Settings loaded")
        _ok(f"database_url = {settings.database_url[:40]}...")
        _ok(f"qdrant_url = {settings.qdrant_url}")
        _ok(f"celery_eager = {settings.celery_always_eager}")
        return True
    except Exception as e:
        _fail("Config", e); return False


def test_database():
    print("\n[2] Database")
    try:
        from sqlalchemy import text
        from db.database import SessionLocal, create_tables
        create_tables()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        _ok("Connected and tables created")
        return True
    except Exception as e:
        _fail("Database", e); return False


def test_groq():
    print("\n[3] Groq API")
    try:
        from providers.llm.groq_provider import GroqProvider
        llm = GroqProvider()
        r = llm.complete(
            messages=[{"role": "user", "content": "Say OK only."}],
            model="llama-3.1-8b-instant",
            max_tokens=5,
        )
        assert r.strip()
        _ok("Groq", f"response='{r.strip()}'")
        return True
    except Exception as e:
        _fail("Groq API", e); return False


def test_embedder():
    print("\n[4] Embedder")
    try:
        from providers.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
        e = SentenceTransformerEmbedder()
        v = e.embed_documents(["hello world"])
        assert len(v[0]) == 384
        _ok("Embedder", "384-dim ✓")
        return True
    except Exception as e:
        _fail("Embedder", e); return False


def test_qdrant():
    print("\n[5] Qdrant")
    try:
        from providers.vectorstores.qdrant_vector_store import QdrantVectorStore
        s = QdrantVectorStore()
        _ok("Qdrant", f"collection='{s.collection}'")
        return True
    except Exception as e:
        _fail("Qdrant", e)
        print("     → Run qdrant.exe  OR  use cloud.qdrant.io")
        return False


def test_bm25():
    print("\n[6] BM25")
    try:
        from providers.keyword.bm25_store import BM25KeywordStore
        BM25KeywordStore()
        _ok("BM25 loaded")
        return True
    except Exception as e:
        _fail("BM25", e); return False


def test_ingestion():
    print("\n[7] Full Ingestion")
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "Python is a high-level programming language. "
                "It is widely used in data science and machine learning. "
                "FastAPI is a modern web framework for building APIs with Python."
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
                original_filename="test_document.txt",
            )
        finally:
            db.close()
            Path(tmp).unlink(missing_ok=True)

        assert result.status == "success", f"status={result.status}"
        assert result.total_chunks > 0
        _ok("Ingestion", f"{result.total_chunks} chunks, file_type={result.file_type}")
        return True
    except Exception as e:
        _fail("Ingestion", e); return False


def test_query():
    print("\n[8] Query Pipeline")
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
            query_text="What is Python used for?",
        )
        assert "answer" in result
        _ok("Query", f"answer={len(result['answer'])} chars, intent={result.get('intent')}")
        return True
    except Exception as e:
        _fail("Query pipeline", e); return False


def test_get_documents():
    print("\n[9] Document List Endpoint")
    try:
        from db.database import SessionLocal
        from db.repository import DocumentRepository

        db = SessionLocal()
        try:
            repo = DocumentRepository(db)
            docs = repo.get_by_user_id("system_test_user")
            _ok("Document fetch", f"{len(docs)} docs for test user")
        finally:
            db.close()
        return True
    except Exception as e:
        _fail("Document list", e); return False


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
        test_ingestion,
        test_query,
        test_get_documents,
    ]

    results = []
    for t in tests:
        try:
            results.append(t())
        except Exception as e:
            print(f"  ✗  Crash in {t.__name__}: {e}")
            results.append(False)

    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "=" * 55)
    print(f"  {passed}/{len(results)} passed,  {failed} failed")
    if failed == 0:
        print("  All systems operational.")
    else:
        print("  Fix failures before starting the server.")
    print("=" * 55)
    sys.exit(0 if failed == 0 else 1)
    