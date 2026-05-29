# backend/api/routes/upload.py — full updated (passes original_filename)
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from agents.ingestion_agent import IngestionAgent
from api.dependencies import get_ingestion_agent
from config import settings
from middleware.clerk_auth import get_verified_user_id
from schemas.api import ErrorResponse, UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Query(..., min_length=1),
    verified_id: str | None = Depends(get_verified_user_id),
    ingestion_agent: IngestionAgent = Depends(get_ingestion_agent),
) -> UploadResponse:

    effective_user_id = verified_id or user_id

    original_filename = file.filename or "unknown"
    suffix = _validate_extension(original_filename)

    content = await file.read(settings.max_upload_bytes + 1)

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=ErrorResponse(
                error="file_too_large",
                detail=f"Max {settings.max_upload_bytes // (1024 * 1024)}MB",
            ).model_dump(),
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(error="empty_file", detail="File has no content").model_dump(),
        )

    save_path = _save_file(content, suffix)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: ingestion_agent.run(
                source=save_path,
                user_id=effective_user_id,
                original_filename=original_filename,  # ← passed here
            ),
        )
    finally:
        save_path.unlink(missing_ok=True)
        await file.close()

    response = UploadResponse(
        document_id=result.document_id,
        file_name=result.file_name,
        total_chunks=result.total_chunks,
        summary=result.summary.short_summary,
        key_topics=result.summary.key_topics,
        status=result.status,
        errors=[e.message for e in result.errors],
    )

    if result.status == "failed":
        raise HTTPException(status_code=422, detail=response.model_dump())

    return response


def _validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="unsupported_file_type",
                detail=f"'{suffix}' is not supported",
            ).model_dump(),
        )
    return suffix


def _save_file(content: bytes, suffix: str) -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid.uuid4()}{suffix}"
    path.write_bytes(content)
    return path
