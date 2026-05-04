from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import grpc
from grpc.aio import Channel

from app.grpc.generated import market_pb2, market_pb2_grpc
from app.domain.exceptions import GrpcClientError

logger = logging.getLogger(__name__)


# DTO — повторяет структуру market-service dto.py, чтобы не создавать зависимость
from dataclasses import dataclass

@dataclass(frozen=True)
class PriceBarDto:
    time:   datetime
    ticker: str
    open:   Optional[Decimal]
    high:   Optional[Decimal]
    low:    Optional[Decimal]
    close:  Decimal
    volume: Optional[int]


@dataclass(frozen=True)
class OHLCVDto:
    ticker:   str
    interval: str
    bars:     tuple[PriceBarDto, ...]


class MarketServiceClient:
    """
    Асинхронный gRPC-клиент для market-service.
    Управление каналом через async context manager.

    Пример:
        async with MarketServiceClient(target="market-service:50051") as client:
            ohlcv = await client.get_ohlcv("AAPL", "1d", from_dt, to_dt)
    """

    def __init__(self, target: str) -> None:
        self._target: str          = target
        self._channel: Channel | None = None
        self._stub:    market_pb2_grpc.MarketServiceStub | None = None

    async def __aenter__(self) -> "MarketServiceClient":
        self._channel = grpc.aio.insecure_channel(self._target)
        self._stub    = market_pb2_grpc.MarketServiceStub(self._channel)
        return self

    async def __aexit__(self, *_) -> None:
        if self._channel:
            await self._channel.close()

    # ── публичное API ─────────────────────────────────────────────────────────

    async def get_ohlcv(
        self,
        ticker:   str,
        interval: str,
        from_dt:  datetime,
        to_dt:    datetime,
    ) -> OHLCVDto:
        """
        Запрашивает OHLCV-свечи у market-service.

        Args:
            ticker:   тикер ценной