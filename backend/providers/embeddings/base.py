from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple passage texts. Empty input returns empty list."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""