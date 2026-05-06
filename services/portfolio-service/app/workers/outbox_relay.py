import asyncio
import logging

from app.core.config import settings
from app.infrastructure.db.session import AsyncSessionFactory
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.outbox.outbox_repo import OutboxRepo
from app.infrastructure.messaging.publisher import PortfolioEventPublisher

logger = logging.getLogger(__name__)


async def run_outbox_relay() -> None:
    """
    Async loop: каждые OUTBOX_RELAY_INTERVAL секунд читает pending Outbox-записи
    и публикует их в RabbitMQ, затем помечает sent_at.
    """
    publisher = PortfolioEventPublisher()
    await publisher.connect()
    logger.info("Outbox relay started, interval=%.1fs", settings.outbox_relay_interval)

    while True:
        try:
            async with AsyncSessionFactory() as session:
                repo = OutboxRepo(session)
                pending = await repo.get_pending(batch_size=50)

                if pending:
                    sent_ids = []
                    for event in pending:
                        try:
                            await publisher.publish(
                                routing_key=event.routing_key,
                                payload=event.payload,
                                message_id=str(event.id),
                            )
                            sent_ids.append(event.id)
                        except Exception as e:
                            logger.error("Failed to publish event %s: %s", event.id, e)

                    if sent_ids:
                        await repo.mark_sent(sent_ids)
                        logger.info("Outbox: published %d events", len(sent_ids))

        except Exception as e:
            logger.error("Outbox relay error: %s", e)

        await asyncio.sleep(settings.outbox_relay_interval)