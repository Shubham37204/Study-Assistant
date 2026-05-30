from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter

from celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["jobs"])

_STATE_MAP = {
    "PENDING":  "pending",
    "STARTED":  "processing",
    "RETRY":    "processing",
    "SUCCESS":  "success",
    "FAILURE":  "failed",
}


@router.get("/{job_id}")
def get_job_status(job_id: str) -> dict:
    result = AsyncResult(job_id, app=celery_app)
    state = _STATE_MAP.get(result.state, "pending")

    response: dict = {"job_id": job_id, "status": state}

    if result.successful():
        response["result"] = result.result

    if result.failed():
        response["error"] = str(result.result)

    return response
