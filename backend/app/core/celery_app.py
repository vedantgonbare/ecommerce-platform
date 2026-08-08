import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "ecommerce",
    broker=redis_url,
    backend=redis_url,
)

from app.modules.orders import tasks  # noqa: F401 — import registers @celery_app.task functions