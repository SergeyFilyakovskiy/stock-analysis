import logging

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings

logger = logging.getLogger(__name__)

_EXCHANGE_NAME = "portfolio.events"


class PortfolioEventPublisher:
    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            _EXCHANGE_NAME,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("PortfolioEventPublisher connected")

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish(self, routing_key: str, payload: str, message_id: str) -> None:
        if self._exchange is None:
            raise RuntimeError("Publisher not connected")
        await self._exchange.publish(
            aio_pika.Message(
                body=payload.encode(),
                message_id=message_id,
                content_type="application/json",
            ),
            routing_key=routing_key,
        )
        logger.debug("Published %s → %s", message_id, routing_key)