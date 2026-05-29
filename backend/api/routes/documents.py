# backend/api/routes/documents.py  (new file)
from __future__ import annotations

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

    # delete from all three stores — order matters:
    # vector + keyword first, then SQL (SQL is the source of truth)
    loop = asyncio.get_running_loop()

    await loop.run_in_executor(
        None,
        lambda: _delete_from_all(document_id, effective_user_id, vector_store, keyword_store, repository),
    )

    return {"deleted": True, "document_id": document_id}


def _delete_from_all(
    document_id: str,
    user_id: str,
    vector_store: BaseVectorStore,
    keyword_store: BaseKeywordStore,
    repository: DocumentRepository,
) -> None:
    try:
        vector_store.delete_document(document_id, user_id)
    except Exception:
        logger.warning("Vector store delete failed for %s", document_id)

    try:
        keyword_store.delete_document(document_id, user_id)
    except Exception:
        logger.warning("Keyword store delete failed for %s", document_id)

    repository.delete(document_id)
    