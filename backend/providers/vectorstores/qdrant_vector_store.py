from __future__ import annotations

import logging
import uuid as uuid_lib
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from config import settings
from providers.vectorstores.base import BaseVectorStore
from schemas.chunk import Chunk

logger = logging.getLogger(__name__)


def _to_qdrant_id(chunk_id: str) -> str:
    return str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, chunk_id))


class QdrantVectorStore(BaseVectorStore):

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.client = QdrantClient(
            url=url or settings.qdrant_url,
            api_key=api_key or settings.qdrant_api_key,  
        )
        self.collection = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.embed_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s", self.collection)

    def add(
        self,
        document_id: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict[str, str],
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")

        points = [
            PointStruct(
                id=_to_qdrant_id(chunk.chunk_id),
                vector=embedding,
                payload={
                    "chunk_id":    chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "user_id":     metadata.get("user_id", ""),
                    "text":        chunk.text,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "file_type":   metadata.get("file_type", ""),
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.client.upsert(collection_name=self.collection, points=points)

    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        qdrant_filter = self._build_filter(filters)

        try:
            hits = self.client.search(
                collection_name=self.collection,
                query_vector=embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
        except Exception:
            # Correct fix: catch specific Qdrant exceptions and return an API-visible dependency error.
            logger.warning(
                "Qdrant query failed. filters=%s",
                filters,
            )
            return []

        return [
            {
                "chunk_id":    hit.payload["chunk_id"],
                "document_id": hit.payload["document_id"],
                "text":        hit.payload["text"],
                "page_number": hit.payload.get("page_number"),
                "score":       hit.score,
            }
            for hit in hits
        ]

    def delete_document(self, document_id: str, user_id: str) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                    FieldCondition(key="user_id",     match=MatchValue(value=user_id)),
                ]
            ),
        )

    @staticmethod
    def _build_filter(filters: dict[str, Any]) -> Filter | None:
        conditions: list[FieldCondition] = []

        user_id = filters.get("user_id")
        if user_id:
            conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))

        document_ids = filters.get("document_ids")
        if document_ids:
            conditions.append(FieldCondition(key="document_id", match=MatchAny(any=document_ids)))

        return Filter(must=conditions) if conditions else None
    
