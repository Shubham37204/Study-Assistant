from __future__ import annotations
import logging
from typing import Any
from core.hybrid_search import HybridSearcher
from schemas.retrieval import ChunkResult, RetrievalResult, SearchQuery  # ← fixed typo
logger = logging.getLogger(__name__)

class RetrievalAgent:
    def __init__(
        self,
        embedder: Any,
        vector_store: Any,
        bm25_store: Any,
        reranker: Any,
    ) -> None:
        self.embedder = embedder
        self.searcher = HybridSearcher(vector_store, bm25_store)
        self.reranker = reranker

    def run(self, query: SearchQuery) -> RetrievalResult:
        try:
            query_embedding = self.embedder.embed_query(query.query_text)

            candidates = self.searcher.search(
                query=query,
                query_embedding=query_embedding,
            )
            candidates_count = len(candidates)

            if candidates and query.search_type != "bm25_only":
                final_chunks = self.reranker.rerank(
                    query=query.query_text,
                    chunks=candidates,
                    top_k=query.top_k,
                )
                reranking_applied = True
            else:
                final_chunks = candidates[: query.top_k]
                reranking_applied = False

            self._log_retrieval_stats(
                query=query,
                candidates=candidates,
                final=final_chunks,
            )

            return RetrievalResult(
                query_text=query.query_text,
                chunks=final_chunks,
                search_type_used=query.search_type,
                total_candidates_before_rerank=candidates_count,
                reranking_applied=reranking_applied,
            )

        except Exception:
            logger.exception(
                "Retrieval failed. user_id=%s search_type=%s query=%r",
                query.user_id,
                query.search_type,
                query.query_text,
            )
            return RetrievalResult(
                query_text=query.query_text,
                chunks=[],
                search_type_used=query.search_type,
                total_candidates_before_rerank=0,
                reranking_applied=False,
            )

    @staticmethod
    def _log_retrieval_stats(
        query: SearchQuery,
        candidates: list[ChunkResult],
        final: list[ChunkResult],
    ) -> None:
        logger.info(
            "Retrieval done. user_id=%s type=%s query=%r candidates=%d final=%d",
            query.user_id,
            query.search_type,
            query.query_text,
            len(candidates),
            len(final),
        )