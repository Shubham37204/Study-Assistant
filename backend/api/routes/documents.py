from __future__ import annotations

import json as _json
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_keyword_store, get_vector_store
from db.repository import DocumentRepository
from middleware.clerk_auth import get_verified_user_id
from providers.keyword.base import BaseKeywordStore
from providers.vectorstores.base import BaseVectorStore

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


def _safe_list(raw) -> list:
    """Convert DB field to list — handles None, list, JSON string."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = _json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (_json.JSONDecodeError, ValueError):
            return []
    return []


def _safe_str(raw, default: str = "") -> str:
    if raw is None:
        return default
    return str(raw)


@router.get("")
async def get_documents(
    user_id: str = Query(..., min_length=1),
    verified_id: str | None = Depends(get_verified_user_id),
    db: Session = Depends(get_db),
) -> list[dict]:
    effective_user_id = verified_id or user_id
    repository = DocumentRepository(db)

    try:
        docs = repository.get_by_user_id(effective_user_id)
    except Exception:
        logger.exception("Failed to fetch documents for user=%s", effective_user_id)
        return []

    result = []
    for d in docs:
        try:
            result.append({
                "document_id":  _safe_str(d.document_id),
                "file_name":    _safe_str(d.file_name, "unknown"),
                "file_type":    _safe_str(getattr(d, "file_type", "text"), "text") or "text",
                "total_chunks": getattr(d, "total_chunks", 0) or 0,
                "summary":      _safe_str(getattr(d, "summary", "")),
                "key_topics":   _safe_list(getattr(d, "key_topics", None)),
                "status":       _safe_str(getattr(d, "status", "success"), "success"),
            })
        except Exception:
            logger.warning("Skipped malformed document record: %s", getattr(d, "document_id", "?"))
            continue

    return result


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Query(..., min_length=1),
    verified_id: str | None = Depends(get_verified_user_id),
    db: Session = Depends(get_db),
    vector_store: BaseVectorStore = Depends(get_vector_store),
    keyword_store: BaseKeywordStore = Depends(get_keyword_store),
) -> dict:
    effective_user_id = verified_id or user_id
    repository = DocumentRepository(db)

    doc = repository.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != effective_user_id:
        raise HTTPException(status_code=403, detail="Not your document")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: _delete_from_all(
            document_id, effective_user_id, vector_store, keyword_store, repository
        ),
    )
    return {"deleted": True, "document_id": document_id}


def _delete_from_all(document_id, user_id, vector_store, keyword_store, repository):
    try:
        vector_store.delete_document(document_id, user_id)
    except Exception:
        logger.warning("Vector store delete failed for %s", document_id)
    try:
        keyword_store.delete_document(document_id, user_id)
    except Exception:
        logger.warning("Keyword store delete failed for %s", document_id)
    repository.delete(document_id)
    