# from __future__ import annotations

# import asyncio
# import logging
# import uuid
# from pathlib import Path
# from middleware.clerk_auth import get_verified_user_id
# from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

# from agents.ingestion_agent import IngestionAgent
# from api.dependencies import get_ingestion_agent
# from config import settings
# from schemas.api import ErrorResponse, UploadResponse

# router = APIRouter(prefix="/upload", tags=["upload"])
# logger = logging.getLogger(__name__)


# @router.post(
#     "",
#     response_model=UploadResponse,
#     responses={
#         400: {"model": ErrorResponse},
#         413: {"model": ErrorResponse},
#         422: {"model": UploadResponse},
#     },
# )
# async def upload_file(
#     user_id: str = Query(..., min_length=1),
#     file: UploadFile = File(...),
#     ingestion_agent: IngestionAgent = Depends(get_ingestion_agent),
# ) -> UploadResponse:
#     suffix = _validate_upload_extension(file.filename)

#     content = await file.read(settings.max_upload_bytes + 1)

#     if len(content) > settings.max_upload_bytes:
#         raise HTTPException(
#             status_code=413,
#             detail=ErrorResponse(
#                 error="file_too_large",
#                 detail=f"File exceeds max size of {settings.max_upload_bytes} bytes.",
#             ).model_dump(),
#         )

#     if not content:
#         raise HTTPException(
#             status_code=400,
#             detail=ErrorResponse(
#                 error="empty_file",
#                 detail="Uploaded file is empty.",
#             ).model_dump(),
#         )

#     save_path = _save_upload_file(content=content, suffix=suffix)

#     try:
#         loop = asyncio.get_running_loop()
#         result = await loop.run_in_executor(
#             None,
#             lambda: ingestion_agent.run(source=save_path, user_id=user_id),
#         )

#     finally:
#         save_path.unlink(missing_ok=True)
#         await file.close()

#     response = UploadResponse(
#         document_id=result.document_id,
#         file_name=result.file_name,
#         total_chunks=result.total_chunks,
#         summary=result.summary.short_summary,
#         key_topics=result.summary.key_topics,
#         status=result.status,
#         errors=[error.message for error in result.errors],
#     )

#     if result.status == "failed":
#         raise HTTPException(
#             status_code=422,
#             detail=response.model_dump(),
#         )

#     return response


# def _validate_upload_extension(filename: str | None) -> str:
#     if not filename:
#         raise HTTPException(
#             status_code=400,
#             detail=ErrorResponse(
#                 error="missing_filename",
#                 detail="Uploaded file must include a filename.",
#             ).model_dump(),
#         )

#     suffix = Path(filename).suffix.lower()

#     if suffix not in settings.allowed_extensions:
#         raise HTTPException(
#             status_code=400,
#             detail=ErrorResponse(
#                 error="unsupported_file_type",
#                 detail=f"Unsupported file type: {suffix or 'unknown'}.",
#             ).model_dump(),
#         )

#     return suffix


# def _save_upload_file(content: bytes, suffix: str) -> Path:
#     internal_id = str(uuid.uuid4())
#     upload_dir = Path(settings.upload_dir)
#     upload_dir.mkdir(parents=True, exist_ok=True)

#     save_path = upload_dir / f"{internal_id}{suffix}"
#     save_path.write_bytes(content)

#     return save_path







# backend/api/routes/upload.py — full updated
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

    # if JWT is present and valid, trust it over the query param
    # if JWT is absent (dev mode / no token), fall back to query param
    effective_user_id = verified_id or user_id

    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User identity required")

    suffix = _validate_extension(file.filename)

    content = await file.read(settings.max_upload_bytes + 1)

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=ErrorResponse(
                error="file_too_large",
                detail=f"Max size is {settings.max_upload_bytes // (1024 * 1024)}MB",
            ).model_dump(),
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="empty_file",
                detail="Uploaded file has no content",
            ).model_dump(),
        )

    save_path = _save_file(content, suffix)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: ingestion_agent.run(source=save_path, user_id=effective_user_id),
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


def _validate_extension(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="missing_filename",
                detail="File must have a name",
            ).model_dump(),
        )
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