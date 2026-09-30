"""
Celery application configuration.

Tasks are defined in tasks/ submodules and auto-discovered.
Workers are started separately: celery -A celery_app worker --loglevel=info
"""

from __future__ import annotations

try:
    from celery import Celery
except ImportError:
    # Graceful fallback for local test runners without celery installed
    class Celery:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.conf = {}

        def task(self, *args, **kwargs):
            def decorator(fn):
                def apply_async(args=None, kwargs=None, **k):
                    class AsyncResult:
                        id = "mock-task-id"
                    return AsyncResult()
                fn.apply_async = apply_async
                fn.delay = lambda *a, **k: fn(*a, **k)
                return fn
            return decorator

from config import settings

celery_app = Celery(
    "mota_scholarship",
    broker=getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
    backend=getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "tasks.document_pipeline",
    ],
)

if hasattr(celery_app, "conf") and hasattr(celery_app.conf, "update"):
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Kolkata",
        enable_utc=True,
        # Retry behaviour for transient failures
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # No automatic periodic tasks (cost control: process only on demand)
        beat_schedule={},
    )
