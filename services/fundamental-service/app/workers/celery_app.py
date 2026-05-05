from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "fundamental",
    broker=settings.redis_url,
    backend=settings.redis_celery_url,
    include=[
        "app.workers.report_importer",
        "app.workers.event_consumer",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "nightly-import-financials": {
            "task": "app.workers.report_importer.import_all_tickers",
            "schedule": crontab(
                hour=settings.CELERY_NIGHTLY_IMPORT_HOUR,
                minute=settings.CELERY_NIGHTLY_IMPORT_MINUTE,
            ),
        },
    },
)
