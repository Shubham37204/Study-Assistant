from __future__ import annotations  

import logging
from typing import Any

import chromadb
from chromadb import Collection

from config import settings
from providers.vectorstores.base import BaseVectorStore
from schemas.chunk import Chunk

logger = logging.getLogger(__name__) 


class ChromaVectorStore(BaseVectorStore):
    COLLECTION_NAME = "study_assistant_chunks"

    def __init__(self, persist_directory: str | None = None) -> None:
        path = persist_directory or settings.chroma_path
        self.client = chromadb.PersistentClient(path=path)
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

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
            raise ValueError("chunks and embeddings must have the same length")

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                **metadata,
                "document_id": chunk.document_id,
                "page_number": str(chunk.page_number or ""),
                "chunk_index": str(chunk.chunk_index),
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        where_filter = self._build_where_filter(filters)

        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=where_filter or None,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            logger.warning("ChromaDB query failed. Returning empty results.")
            return []  

        return self._map_query_results(results)

    def delete_document(self, document_id: str, user_id: str) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"user_id": {"$eq": user_id}},
                ]
            }
        )

    @staticmethod
    def _build_where_filter(filters: dict[str, Any]) -> dict[str, Any]:
        conditions: list[dict[str, Any]] = []

        user_id = filters.get("user_id")
        if user_id:
            conditions.append({"user_id": {"$eq": user_id}})

        document_ids = filters.get("document_ids")
        if document_ids:
            conditions.append({"document_id": {"$in": document_ids}})

        if not conditions:
            return {}

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    @staticmethod
    def _map_query_results(results: dict[str, Any]) -> list[dict[str, Any]]:
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        mapped: list[dict[str, Any]] = []

        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            metadata = metadata or {}
            page_number_raw = metadata.get("page_number")
            page_number = int(page_number_raw) if page_number_raw else None

            mapped.append({
                "chunk_id": chunk_id,
                "document_id": metadata.get("document_id", ""),
                "text": document,
                "page_number": page_number,
                "score": 1.0 - float(distance),
            })

        return mapped