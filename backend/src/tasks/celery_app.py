from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "file_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.tasks.scan",
        "src.tasks.metadata",
        "src.tasks.alerts",
    ],
)
