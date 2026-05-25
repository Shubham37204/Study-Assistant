# backend/test_pipeline.py
# run:
#   $env:GROQ_API_KEY = "your_key"
#   python test_pipeline.py

from __future__ import annotations

import tempfile
from pathlib import Path

from agents.ingestion_agent import IngestionAgent
from agents.retrieval_agent import RetrievalAgent
from core.chunker import Chunker
from core.reranker import Reranker
from db.database import create_tables, get_session
from db.repository import DocumentRepository
from providers.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from providers.keyword.bm25_store import BM25KeywordStore
from providers.llm.groq_provider import GroqProvider
from providers.vectorstores.chroma_vector_store import ChromaVectorStore
from schemas.retrieval import SearchQuery

# ── setup ──────────────────────────────────────────────────────────────────────

create_tables()

llm           = GroqProvider()
embedder      = SentenceTransformerEmbedder()
chunker       = Chunker()
vector_store  = ChromaVectorStore()
keyword_store = BM25KeywordStore()
reranker      = Reranker()

db            = get_session()
repository    = DocumentRepository(db)

ingestion_agent = IngestionAgent(
    repository=repository,
    llm=llm,
    chunker=chunker,
    embedder=embedder,
    vector_store=vector_store,
    keyword_store=keyword_store,
)

retrieval_agent = RetrievalAgent(
    embedder=embedder,
    vector_store=vector_store,
    bm25_store=keyword_store,
    reranker=reranker,
)

USER_ID = "test_user_1"

# ── M2: ingest ─────────────────────────────────────────────────────────────────

NOTE_CONTENT = """
Newton's Laws of Motion

Newton's first law states that an object at rest stays at rest and an
object in motion stays in motion unless acted upon by a net external force.

Newton's second law states that force equals mass times acceleration.
The formula is F = ma. This is the most commonly used equation in mechanics.

Newton's third law states that for every action there is an equal and
opposite reaction. If object A exerts a force on object B, then B exerts
an equal and opposite force on A.

Gravitation

The law of universal gravitation states that every mass attracts every
other mass. The gravitational force is proportional to the product of the
masses and inversely proportional to the square of the distance between them.
F = G * m1 * m2 / r^2
"""

with tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", delete=False, encoding="utf-8"
) as f:
    f.write(NOTE_CONTENT)
    tmp_path = f.name

print("\n── M2: Ingestion ──────────────────────────────────────────────────")
result = ingestion_agent.run(source=tmp_path, user_id=USER_ID)
Path(tmp_path).unlink()

print(f"status        : {result.status}")
print(f"document_id   : {result.document_id}")
print(f"total_chunks  : {result.total_chunks}")
print(f"summary       : {result.summary.short_summary}")
print(f"topics        : {result.summary.key_topics}")
print(f"errors        : {result.errors}")

assert result.status == "success", f"Ingestion failed: {result.errors}"
assert result.total_chunks > 0,    "No chunks produced"

DOC_ID = result.document_id

# ── M3: hybrid vs vector_only ──────────────────────────────────────────────────

QUERY = "Newton second law formula F equals ma"

print("\n── M3: Hybrid Search ──────────────────────────────────────────────")
hybrid_result = retrieval_agent.run(SearchQuery(
    query_text=QUERY,
    user_id=USER_ID,
    document_ids=[DOC_ID],
    search_type="hybrid",
    top_k=3,
))

print(f"candidates before rerank : {hybrid_result.total_candidates_before_rerank}")
print(f"reranking applied        : {hybrid_result.reranking_applied}")
print(f"chunks returned          : {len(hybrid_result.chunks)}")
for i, chunk in enumerate(hybrid_result.chunks):
    print(f"  [{i+1}] score={chunk.score:.4f} sources={chunk.retrieval_sources} page={chunk.page_number}")
    print(f"       {chunk.text[:120].strip()!r}")

print("\n── M3: Vector Only ────────────────────────────────────────────────")
vector_result = retrieval_agent.run(SearchQuery(
    query_text=QUERY,
    user_id=USER_ID,
    document_ids=[DOC_ID],
    search_type="vector_only",
    top_k=3,
))

print(f"chunks returned : {len(vector_result.chunks)}")
for i, chunk in enumerate(vector_result.chunks):
    print(f"  [{i+1}] score={chunk.score:.4f} sources={chunk.retrieval_sources} page={chunk.page_number}")
    print(f"       {chunk.text[:120].strip()!r}")

# ── verification ───────────────────────────────────────────────────────────────

print("\n── Verification ───────────────────────────────────────────────────")
if hybrid_result.chunks:
    top = hybrid_result.chunks[0]
    found_by_both = set(top.retrieval_sources) == {"vector", "bm25"}
    print(f"Top chunk sources : {top.retrieval_sources}")
    print(f"Found by both     : {found_by_both}  ← proves hybrid > vector_only")

db.close()
print("\n✓ M2 + M3 complete")
