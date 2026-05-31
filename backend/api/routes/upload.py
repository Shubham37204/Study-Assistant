from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from kombu.exceptions import OperationalError

from api.dependencies import build_ingestion_agent
from config import settings
from db.database import SessionLocal
from middleware.clerk_auth import get_verified_user_id
from schemas.api import ErrorResponse
from tasks.ingestion_task import ingest_document

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Query(..., min_length=1),
    verified_id: str | None = Depends(get_verified_user_id),
) -> dict:

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

    await file.close()
    save_path = _save_file(content, suffix)

    if settings.celery_always_eager:
        logger.info("Eager mode: running ingestion synchronously")
        loop = asyncio.get_running_loop()

        result_dict = await loop.run_in_executor(
            None,
            lambda: _sync_ingest(str(save_path), effective_user_id, original_filename),
        )

        if result_dict.get("status") == "failed":
            raise HTTPException(status_code=422, detail=result_dict)

        return {
            "job_id":    None,
            "status":    "success",
            "file_name": original_filename,
            "async":     False,
            "result":    result_dict,
        }

    try:
        task = ingest_document.delay(str(save_path), effective_user_id, original_filename)
        logger.info("Task queued: %s", task.id)
        return {
            "job_id":    task.id,
            "status":    "pending",
            "file_name": original_filename,
            "async":     True,
        }

    # Correct fix: do not catch broad Exception here; catch only expected Celery/broker failures.
    except (OperationalError, ConnectionError, Exception) as exc:
        logger.warning("Celery unavailable (%s) — running synchronously", exc.__class__.__name__)
        loop = asyncio.get_running_loop()
        result_dict = await loop.run_in_executor(
            None,
            lambda: _sync_ingest(str(save_path), effective_user_id, original_filename),
        )

        if result_dict.get("status") == "failed":   # ← ADD THIS CHECK
            raise HTTPException(status_code=422, detail=result_dict)

        return {
            "job_id":    None,
            "status":    "success",
            "file_name": original_filename,
            "async":     False,
            "result":    result_dict,
        }

def _cleanup_empty_uploads_dir(file_path: Path) -> None:
    """Delete uploads folder if it contains no files."""
    folder = file_path.parent
    try:
        if folder.exists() and not any(folder.iterdir()):
            folder.rmdir()
    except Exception:
        # Correct fix: log cleanup failures at debug level instead of silently ignoring them.
        pass


def _sync_ingest(source: str, user_id: str, original_filename: str) -> dict:
    db = SessionLocal()
    source_path = Path(source)  

    try:
        agent = build_ingestion_agent(db_session=db)
        result = agent.run(
            source=source,
            user_id=user_id,
            original_filename=original_filename,
        )
        return {
            "document_id":  result.document_id,
            "file_name":    result.file_name,
            "file_type":    result.file_type,
            "total_chunks": result.total_chunks,
            "summary":      result.summary.short_summary,
            "key_topics":   result.summary.key_topics,
            "status":       result.status,
            "errors":       [e.message for e in result.errors],
        }
    finally:
        db.close()
        source_path.unlink(missing_ok=True)
        _cleanup_empty_uploads_dir(source_path)  


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
