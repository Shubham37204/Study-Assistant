from __future__ import annotations

from typing import Any

from schemas.retrieval import ChunkResult, SearchQuery


class HybridSearcher:
    RRF_K = 60

    def __init__(self, vector_store: Any, bm25_store: Any) -> None:
        self.vector_store = vector_store
        self.bm25_store = bm25_store

    def search(
        self,
        query: SearchQuery,
        query_embedding: list[float],
    ) -> list[ChunkResult]:
        filters = self._build_filters(query)

        if query.search_type == "vector_only":
            return self._vector_search(query_embedding, query, filters)

        if query.search_type == "bm25_only":
            return self._bm25_search(query, filters)

        vector_results = self._vector_search(query_embedding, query, filters)
        bm25_results = self._bm25_search(query, filters)

        fused_results = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            bm25_results=bm25_results,
        )

        return fused_results[: query.vector_fetch_k]

    @staticmethod
    def _build_filters(query: SearchQuery) -> dict[str, Any]:
        filters: dict[str, Any] = {
            "user_id": query.user_id,
        }

        if query.document_ids:
            filters["document_ids"] = query.document_ids

        return filters

    def _vector_search(
        self,
        embedding: list[float],
        query: SearchQuery,
        filters: dict[str, Any],
    ) -> list[ChunkResult]:
        results = self.vector_store.query(
            embedding=embedding,
            top_k=query.vector_fetch_k,
            filters=filters,
        )

        return [
            self._to_chunk_result(
                result,
                retrieval_sources=["vector"],
            )
            for result in results
        ]

    def _bm25_search(
        self,
        query: SearchQuery,
        filters: dict[str, Any],
    ) -> list[ChunkResult]:
        results = self.bm25_store.query(
            query_text=query.query_text,
            top_k=query.vector_fetch_k,
            filters=filters,
        )

        return [
            self._to_chunk_result(
                result,
                retrieval_sources=["bm25"],
            )
            for result in results
        ]

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[ChunkResult],
        bm25_results: list[ChunkResult],
    ) -> list[ChunkResult]:
        scores: dict[str, float] = {}
        merged_chunks: dict[str, ChunkResult] = {}

        self._accumulate_rrf_scores(
            results=vector_results,
            scores=scores,
            merged_chunks=merged_chunks,
        )
        self._accumulate_rrf_scores(
            results=bm25_results,
            scores=scores,
            merged_chunks=merged_chunks,
        )

        reranked_chunks = [
            ChunkResult.model_validate(
                {
                    **chunk.model_dump(),
                    "score": scores[chunk_id],
                }
            )
            for chunk_id, chunk in merged_chunks.items()
        ]

        return sorted(
            reranked_chunks,
            key=lambda chunk: chunk.score,
            reverse=True,
        )

    def _accumulate_rrf_scores(
        self,
        results: list[ChunkResult],
        scores: dict[str, float],
        merged_chunks: dict[str, ChunkResult],
    ) -> None:
        for rank, chunk in enumerate(results, start=1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + (
                1.0 / (self.RRF_K + rank)
            )

            existing_chunk = merged_chunks.get(chunk.chunk_id)

            if existing_chunk is None:
                merged_chunks[chunk.chunk_id] = chunk
                continue

            merged_sources = self._merge_sources(
                existing_chunk.retrieval_sources,
                chunk.retrieval_sources,
            )

            merged_chunks[chunk.chunk_id] = ChunkResult.model_validate(
                {
                    **existing_chunk.model_dump(),
                    "retrieval_sources": merged_sources,
                }
            )

    @staticmethod
    def _merge_sources(
        existing_sources: list[str],
        new_sources: list[str],
    ) -> list[str]:
        ordered_sources: list[str] = []

        for source in [*existing_sources, *new_sources]:
            if source not in ordered_sources:
                ordered_sources.append(source)

        return ordered_sources

    @staticmethod
    def _to_chunk_result(
        result: Any,
        retrieval_sources: list[str],
    ) -> ChunkResult:
        if isinstance(result, ChunkResult):
            return ChunkResult.model_validate(
                {
                    **result.model_dump(),
                    "retrieval_sources": retrieval_sources,
                }
            )

        if isinstance(result, dict):
            return ChunkResult.model_validate(
                {
                    **result,
                    "retrieval_sources": retrieval_sources,
                }
            )

        return ChunkResult.model_validate(
            {
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "text": result.text,
                "page_number": getattr(result, "page_number", None),
                "score": getattr(result, "score", 0.0),
                "retrieval_sources": retrieval_sources,
            }
        )