import json
import uuid
from datetime import datetime
from decimal import Decimal

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings


class MarketEventPublisher:

    EXCHANGE_NAME = "market.events"

    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractConnection
        self._channel:    aio_pika.abc.AbstractChannel
        self._exchange:   aio_pika.abc.AbstractExchange

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel    = await self._connection.channel()
        self._exchange   = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            ExchangeType.TOPIC,
            durable=True,
        )

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish_price_updated(
        self,
        ticker:    str,
        price:     Decimal,
        timestamp: datetime,
    ) -> None:
        event_id = str(uuid.uuid4())
        payload = json.dumps({
            "event_id":  event_id,
            "event":     "price.updated",
            "ticker":    ticker.upper(),
            "price":     str(price),
            "timestamp": timestamp.isoformat(),
            "source":    "market-service",
        })
        await self._exchange.publish(
            aio_pika.Message(
                body=payload.encode(),
                message_id=event_id,
                content_type="application/json",
            ),
            routing_key=f"price.updated.{ticker.upper()}",
        )