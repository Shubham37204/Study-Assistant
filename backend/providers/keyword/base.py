from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from schemas.chunk import Chunk


class BaseKeywordStore(ABC):
    @abstractmethod
    def add(self, document_id: str, chunks: list[Chunk]) -> None:
        """Store chunks for keyword retrieval."""
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        query_text: str,
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return ranked chunk dictionaries for keyword search."""
        raise NotImplementedError

    @abstractmethod
    def delete_document(self, document_id: str, user_id: str) -> None:
        """Delete keyword index entries only when owned by the given user."""
        raise NotImplementedError
    