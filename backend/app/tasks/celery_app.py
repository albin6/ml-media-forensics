from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "forensics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.image_task.*": {"queue": "image_queue"},
        "app.tasks.video_task.*": {"queue": "video_queue"},
    },
    task_time_limit=600,
    task_soft_time_limit=540,
)
