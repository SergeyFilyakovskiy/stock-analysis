import json
import logging
from datetime import date
from decimal import Decimal

import aio_pika

from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportPublisher:
    """
    Observer/Publisher: публикует событие report.published в RabbitMQ
    после успешного импорта финансового отчёта.

    Подписчики (notification-service) получают событие и отправляют
    WebSocket-уведомление клиентам.
    """

    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("ReportPublisher connected to RabbitMQ")

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish_report_imported(
        self,
        ticker: str,
        period: str,
        fiscal_year: int,
        source: str = "polygon",
    ) -> None:
        """Публикует событие после импорта отчёта."""
        if self._channel is None:
            await self.connect()

        payload = {
            "event": "report.published",
            "ticker": ticker,
            "period": period,
            "fiscal_year": fiscal_year,
            "source": source,
        }
        exchange = await self._channel.get_exchange(settings.RABBITMQ_EXCHANGE) # type: ignore
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=settings.RABBITMQ_REPORT_QUEUE,
        )
        logger.debug("Published report.published for %s period=%s", ticker, period)
