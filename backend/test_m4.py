# backend/test_m4.py
from graph.rag_graph import RAGGraph
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.bm25_store import BM25Store
from core.reranker import Reranker

graph = RAGGraph(Embedder(), VectorStore(), BM25Store(), Reranker())

result = graph.query(
    user_id="test_user_1",
    query_text="What is Newton's second law?",
    document_ids=[],
)

print(result["answer"])
print(result["citations"])
# verify: answer cites sources, no hallucination, citations have page numbers