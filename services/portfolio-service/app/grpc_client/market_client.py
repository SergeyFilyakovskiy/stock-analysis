from __future__ import annotations

import logging
from decimal import Decimal

import grpc
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.grpc_client.generated import market_pb2, market_pb2_grpc

logger = logging.getLogger(__name__)

_RETRYABLE = (
    grpc.RpcError,
    ConnectionError,
)


class MarketGrpcClient:
    """
    gRPC-клиент к market-service.
    Circuit breaker через tenacity: 3 попытки с exponential backoff.
    При недоступности возвращает пустой dict (fallback → берём цены из Redis).
    """

    def __init__(self) -> None:
        self._address = settings.grpc_address
        self._timeout = settings.grpc_timeout

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=False,
    )
    async def get_last_price_batch(
        self, tickers: list[str]
    ) -> dict[str, Decimal]:
        """
        Возвращает {TICKER: Decimal(price)}.
        При ошибке после всех retry → возвращает {}.
        """
        if not tickers:
            return {}

        try:
            async with grpc.aio.insecure_channel(self._address) as channel:
                stub = market_pb2_grpc.MarketServiceStub(channel)
                request = market_pb2.GetLastPriceBatchRequest(
                    tickers=[t.upper() for t in tickers]
                )
                response = await stub.GetLastPriceBatch(
                    request, timeout=self._timeout
                )
                return {
                    item.ticker: Decimal(item.price)
                    for item in response.prices
                    if item.price
                }
        except grpc.RpcError as e:
            logger.warning(
                "gRPC GetLastPriceBatch failed (status=%s): %s",
                e.code(),
                e.details(),
            )
            return {}
        except Exception as e:
            logger.error("Unexpected gRPC error: %s", e)
            return {}