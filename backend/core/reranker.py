from __future__ import annotations
from typing import Any
from sentence_transformers import CrossEncoder
from schemas.retrieval import ChunkResult


class Reranker:
    MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MAX_LENGTH = 512

    def __init__(self) -> None:
        self._model: CrossEncoder | None = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(
                self.MODEL,
                max_length=self.MAX_LENGTH,
            )

        return self._model

    def rerank(
        self,
        query: str,
        chunks: list[ChunkResult],
        top_k: int,
    ) -> list[ChunkResult]:
        if not chunks:
            return []

        pairs = [(query, chunk.text) for chunk in chunks]
        scores = self.model.predict(pairs)

        reranked_chunks = [
            self._copy_with_score(chunk, score)
            for chunk, score in zip(chunks, scores, strict=True)
        ]

        return sorted(
            reranked_chunks,
            key=lambda chunk: chunk.score,
            reverse=True,
        )[:top_k]

    @staticmethod
    def _copy_with_score(chunk: ChunkResult, score: Any) -> ChunkResult:
        return ChunkResult.model_validate(
            {
                **chunk.model_dump(),
                "score": float(score),
            }
        )