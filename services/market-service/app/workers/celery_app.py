from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "market_data_worker",
    broker=settings.rabbitmq_url,
    backend="rpc://",
    include=["app.workers.price_fetcher"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "fetch-all-prices": {
            "task": "workers.fetch_all_prices",
            "schedule": settings.PRICE_FETCH_INTERVAL_SECONDS,
        },
    },
)