from celery import Celery
from config import settings

celery_app = Celery(
    "study_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.ingestion_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.celery_always_eager,
    task_eager_propagates=True,
)
