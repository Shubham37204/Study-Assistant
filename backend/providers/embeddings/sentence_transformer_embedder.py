from __future__ import annotations

from typing import cast
from sentence_transformers import SentenceTransformer
from config import settings
from providers.embeddings.base import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embed_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=settings.embed_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        return cast(list[list[float]], embeddings.tolist())

    def embed_query(self, text: str) -> list[float]:
        query_text = f"{self.QUERY_PREFIX}{text.strip()}"

        embedding = self.model.encode(
            query_text,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        return cast(list[float], embedding.tolist())