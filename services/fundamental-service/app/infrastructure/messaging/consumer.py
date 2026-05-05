import json
import logging
import json as _json
import aio_pika

from app.core.config import settings

logger = logging.getLogger(__name__)


async def consume_price_events(on_new_ticker_callback) -> None:
    """
    Слушает price.updated от market-service.
    При обнаружении нового тикера → запускает import_financial_report_for_ticker.
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue(
        settings.RABBITMQ_PRICE_QUEUE,
        durable=True,
    )
    logger.info("Listening on queue: %s", settings.RABBITMQ_PRICE_QUEUE)

    async with queue.iterator() as q_iter:
        async for message in q_iter:
            async with message.process():
                try:
                    data = json.loads(message.body)
                    ticker = data.get("ticker")
                    if ticker:
                        await on_new_ticker_callback(ticker)
                except Exception as e:
                    logger.error("Error processing price.updated: %s", e)


def parse_price_event(body: bytes) -> str | None:
    """Парсит тело RabbitMQ-сообщения и извлекает тикер."""
    try:
        data = _json.loads(body.decode())
        return data.get("symbol")
    except Exception:
        return None