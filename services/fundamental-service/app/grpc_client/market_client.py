from __future__ import annotations

import logging
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime

import grpc

from app.core.config import settings
from app.domain.exceptions import MarketServiceError
from app.grpc_client.generated import market_pb2, market_pb2_grpc

logger = logging.getLogger(__name__)


@dataclass
class OHLCVCandle:
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class MarketServiceClient:
    """
    gRPC-клиент для market-service.
    Методы: GetOHLCV, GetLastPrice.
    Используется для расчёта beta, волатильности и актуальной цены акции.
    """

    def __init__(self) -> None:
        self._address = f"{settings.MARKET_SERVICE_HOST}:{settings.MARKET_SERVICE_PORT}"
        self._timeout = settings.GRPC_TIMEOUT

    def _get_stub(self) -> market_pb2_grpc.MarketServiceStub:
        channel = grpc.aio.insecure_channel(self._address)
        return market_pb2_grpc.MarketServiceStub(channel)

    async def get_last_price(self, symbol: str) -> Decimal:
        """Получить последнюю цену акции для расчётов мультипликаторов."""
        stub = self._get_stub()
        try:
            response = await stub.GetLastPrice(
                market_pb2.LastPriceRequest(symbol=symbol),
                timeout=self._timeout,
            )
            return Decimal(str(response.price))
        except grpc.RpcError as e:
            raise MarketServiceError(
                "GetLastPrice",
                f"symbol={symbol} code={e.code()} detail={e.details()}",
            ) from e

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1D",
        limit: int = 252,
    ) -> list[OHLCVCandle]:
        """Получить OHLCV-свечи (для расчёта beta, волатильности в DCF)."""
        stub = self._get_stub()
        try:
            response = await stub.GetOHLCV(
                market_pb2.OHLCVRequest(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                ),
                timeout=self._timeout,
            )
            return [
                OHLCVCandle(
                    timestamp=c.timestamp,
                    open=Decimal(str(c.open)),
                    high=Decimal(str(c.high)),
                    low=Decimal(str(c.low)),
                    close=Decimal(str(c.close)),
                    volume=int(c.volume),
                )
                for c in response.candles
            ]
        except grpc.RpcError as e:
            raise MarketServiceError(
                "GetOHLCV",
                f"symbol={symbol} code={e.code()} detail={e.details()}",
            ) from e
