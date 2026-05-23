from __future__ import annotations
from typing import cast
from sentence_transformers import SentenceTransformer


class Embedder:
    MODEL = "BAAI/bge-small-en-v1.5"
    BATCH_SIZE = 32
    QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.MODEL)

        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.BATCH_SIZE,
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