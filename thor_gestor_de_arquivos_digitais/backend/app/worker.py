from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "thor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.instrumento_indexacao"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="indexacao",
)
