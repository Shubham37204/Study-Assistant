from __future__ import annotations

import logging
from pathlib import Path

from celery_app import celery_app
from config import settings
from db.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.ingest_document",
    max_retries=2,
    default_retry_delay=30,
)
def ingest_document(
    self,
    source_path: str,
    user_id: str,
    original_filename: str,
) -> dict:
    """
    Runs in a Celery worker process — completely isolated from the API process.
    Creates its own DB session and service instances.
    Returns a JSON-serializable dict matching IngestionResult shape.
    """
    db = SessionLocal()

    try:
        from api.dependencies import build_ingestion_agent

        agent = build_ingestion_agent(db_session=db)
        result = agent.run(
            source=source_path,
            user_id=user_id,
            original_filename=original_filename,
        )

        import json
        return json.loads(result.model_dump_json())

    except Exception as exc:
        logger.exception("Ingestion task failed. file=%s", original_filename)
        raise self.retry(exc=exc)

    finally:
        db.close()
        Path(source_path).unlink(missing_ok=True)
        