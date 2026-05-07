# app/infrastructure/messaging/report_consumer.py

import json
import logging
from collections.abc import Callable, Awaitable

import aio_pika

from app.core.config import settings
from app.infrastructure.messaging.schemas import ReportPublishedEvent

logger = logging.getLogger(__name__)

_EXCHANGE_NAME = "portfolio.events"
_QUEUE_NAME    = "notification-service.report.published"
_ROUTING_KEY   = "report.published"


async def consume_report_events(
    on_report_published: Callable[[ReportPublishedEvent], Awaitable[None]],
) -> None:
    """
    Слушает report.published.
    Вызывает on_report_published(event) для каждого нового события.
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel    = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        _EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(_QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=_ROUTING_KEY)

    logger.info("Listening on queue: %s", _QUEUE_NAME)

    seen_ids: set[str] = set()

    async with queue.iterator() as q_iter:
        async for message in q_iter:
            async with message.process():
                try:
                    msg_id = message.message_id or ""
                    if msg_id and msg_id in seen_ids:
                        logger.debug("Duplicate report skipped: %s", msg_id)
                        continue

                    event = ReportPublishedEvent.from_dict(json.loads(message.body))
                    await on_report_published(event)

                    if msg_id:
                        seen_ids.add(msg_id)
                        if len(seen_ids) > 10_000:
                            seen_ids.clear()

                except Exception:
                    logger.exception("Error processing report.published")