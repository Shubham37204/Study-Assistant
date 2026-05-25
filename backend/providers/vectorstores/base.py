from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from schemas.chunk import Chunk

class BaseVectorStore(ABC):
    @abstractmethod
    def add(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict[str, str],
    ) -> None:
        """Store chunk texts, embeddings, and metadata."""
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return ranked chunk dictionaries for the given query embedding."""
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: str, user_id: str) -> None:
        """Delete vectors only when the document belongs to the given user."""
        raise NotImplementedError