from __future__ import annotations

from functools import lru_cache
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from agents.ingestion_agent import IngestionAgent
from core.chunker import Chunker
from core.reranker import Reranker
from db.database import SessionLocal
from db.repository import DocumentRepository
from graph.rag_graph import RAGGraph
from providers.embeddings.sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)
from providers.keyword.bm25_store import BM25KeywordStore
from providers.llm.groq_provider import GroqProvider
from providers.vectorstores.chroma_vector_store import ChromaVectorStore


@lru_cache(maxsize=1)
def get_llm() -> GroqProvider:
    return GroqProvider()


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder()


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    return ChromaVectorStore()


@lru_cache(maxsize=1)
def get_keyword_store() -> BM25KeywordStore:
    return BM25KeywordStore()


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker()


@lru_cache(maxsize=1)
def get_chunker() -> Chunker:
    return Chunker()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_ingestion_agent(
    db: Session = Depends(get_db),
    llm: GroqProvider = Depends(get_llm),
    chunker: Chunker = Depends(get_chunker),
    embedder: SentenceTransformerEmbedder = Depends(get_embedder),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
    keyword_store: BM25KeywordStore = Depends(get_keyword_store),
) -> IngestionAgent:
    repository = DocumentRepository(db)

    return IngestionAgent(
        repository=repository,
        llm=llm,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        keyword_store=keyword_store,
    )


def get_rag_graph(
    llm: GroqProvider = Depends(get_llm),
    embedder: SentenceTransformerEmbedder = Depends(get_embedder),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
    keyword_store: BM25KeywordStore = Depends(get_keyword_store),
    reranker: Reranker = Depends(get_reranker),
) -> RAGGraph:
    return RAGGraph(
        llm=llm,
        embedder=embedder,
        vector_store=vector_store,
        keyword_store=keyword_store,
        reranker=reranker,
    )