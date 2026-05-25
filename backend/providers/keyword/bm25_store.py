from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any
from rank_bm25 import BM25Okapi
from config import settings
from providers.keyword.base import BaseKeywordStore
from schemas.chunk import Chunk

logger = logging.getLogger(__name__)


class BM25KeywordStore(BaseKeywordStore):
    INDEX_FILE_NAME = "index.json"

    def __init__(self, persist_directory: str | None = None) -> None:
        path = persist_directory or settings.bm25_path
        self.persist_path = Path(path)
        self.persist_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.persist_path / self.INDEX_FILE_NAME
        self._lock = threading.Lock()
        self._index_data: dict[str, dict[str, Any]] = {}

        self._load()

    def add(self, document_id: str, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        user_id = chunks[0].metadata.get("user_id")

        if not user_id:
            raise ValueError("Chunk metadata must include user_id")

        with self._lock:
            self._index_data[document_id] = {
                "chunks": [chunk.model_dump() for chunk in chunks],
                "user_id": user_id,
            }
            self._save()

    def query(
        self,
        query_text: str,
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates = self._collect_candidates(filters)

        if not candidates:
            return []

        tokenized_corpus = [chunk["text"].lower().split() for chunk in candidates]
        tokenized_query = query_text.lower().split()

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        scored_candidates = sorted(
            zip(candidates, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        return [
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
                "page_number": chunk.get("page_number"),
                "score": float(score),
            }
            for chunk, score in scored_candidates[:top_k]
        ]

    def delete_document(self, document_id: str, user_id: str) -> None:
        with self._lock:
            entry = self._index_data.get(document_id)

            if entry is None:
                return

            if entry.get("user_id") != user_id:
                return

            self._index_data.pop(document_id)
            self._save()

    def _collect_candidates(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        user_id = filters.get("user_id")

        if not user_id:
            return []

        document_ids = set(filters.get("document_ids") or [])
        candidates: list[dict[str, Any]] = []

        for document_id, entry in self._index_data.items():
            if entry.get("user_id") != user_id:
                continue

            if document_ids and document_id not in document_ids:
                continue

            chunks = entry.get("chunks", [])
            candidates.extend(chunks)

        return candidates

    def _save(self) -> None:
        temp_file = self.index_file.with_suffix(".tmp")
        payload = json.dumps(
            self._index_data,
            ensure_ascii=False,
            indent=2,
        )

        temp_file.write_text(payload, encoding="utf-8")
        temp_file.replace(self.index_file)

    def _load(self) -> None:
        if not self.index_file.exists():
            self._index_data = {}
            return

        try:
            self._index_data = json.loads(
                self.index_file.read_text(encoding="utf-8")
            )

        except json.JSONDecodeError:
            logger.warning(
                "BM25 index file is corrupt. Starting with empty index. path=%s",
                self.index_file,
            )
            self._index_data = {}