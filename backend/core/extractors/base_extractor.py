from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from schemas.ingestion import ExtractedDocument


class ExtractorError(Exception):
    def __init__(self, source: str | Path, reason: str) -> None:
        self.source = str(source)
        self.reason = reason
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"[ExtractorError] {self.source}: {self.reason}"


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, source: str | Path) -> ExtractedDocument:
        """Extract content from one supported source type."""
