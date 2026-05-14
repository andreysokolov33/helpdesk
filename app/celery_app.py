from __future__ import annotations

from celery import Celery
from app.config import settings


def make_celery() -> Celery:
    c = Celery(
        "oss",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[],  # задачи добавляются по мере появления
    )
    c.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        broker_connection_retry_on_startup=True,
    )
    return c


celery_app = make_celery()
