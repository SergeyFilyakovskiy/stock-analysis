import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.event_consumer.start_price_event_consumer",
)
def start_price_event_consumer() -> None:
    """Запускает слушатель price.updated из RabbitMQ."""
    asyncio.run(_consume())


async def _consume() -> None:
    from app.infrastructure.messaging.consumer import consume_price_events
    from app.infrastructure.db.repositories.company_repo import CompanyRepo
    from app.infrastructure.db.session import AsyncSessionFactory
    from app.workers.report_importer import import_financial_report_for_ticker

    async def on_new_ticker(ticker: str) -> None:
        async with AsyncSessionFactory() as session:
            exists = await CompanyRepo(session).exists(ticker)
        if not exists:
            logger.info("New ticker discovered: %s — triggering import", ticker)
            import_financial_report_for_ticker.delay(ticker) # type: ignore

    await consume_price_events(on_new_ticker)
