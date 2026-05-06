import json
import logging

import aio_pika

from app.core.config import settings
from app.infrastructure.messaging.schemas import PriceUpdatedEvent

logger = logging.getLogger(__name__)

_EXCHANGE_NAME = "market.events"
_QUEUE_NAME = "portfolio-service.price.updated"
_ROUTING_KEY = "price.updated.#"


async def consume_price_events(on_price_updated) -> None:
    """
    Слушает price.updated.* от market-service.
    on_price_updated(event: PriceUpdatedEvent) → проверяет алерты.
    Дедупликация по message_id (aio_pika делает ack только после успешной обработки).
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        _EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(_QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=_ROUTING_KEY)

    logger.info("Listening on queue: %s", _QUEUE_NAME)

    seen_ids: set[str] = set()   # in-memory дедупликация в рамках одного запуска

    async with queue.iterator() as q_iter:
        async for message in q_iter:
            async with message.process():
                try:
                    msg_id = message.message_id or ""
                    if msg_id and msg_id in seen_ids:
                        logger.debug("Duplicate message skipped: %s", msg_id)
                        continue

                    data = json.loads(message.body)
                    event = PriceUpdatedEvent.from_dict(data)

                    await on_price_updated(event)

                    if msg_id:
                        seen_ids.add(msg_id)
                        if len(seen_ids) > 10_000:
                            seen_ids.clear()

                except Exception as e:
                    logger.error("Error processing price.updated: %s", e)