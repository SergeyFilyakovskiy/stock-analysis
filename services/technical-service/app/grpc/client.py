from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import grpc
from grpc.aio import Channel

from app.grpc.generated import market_pb2, market_pb2_grpc
from app.domain.exceptions import GrpcClientError

logger = logging.getLogger(__name__)


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

    def __init__(self, target: str) -> None:
        self._target: str = target
        self._channel: Channel | None = None
        self._stub: market_pb2_grpc.MarketServiceStub | None = None

    async def __aenter__(self) -> "MarketServiceClient":
        self._channel = grpc.aio.insecure_channel(self._target)
        self._stub    = market_pb2_grpc.MarketServiceStub(self._channel)
        return self

    async def __aexit__(self, *_) -> None:
        if self._channel:
            await self._channel.close()

    async def get_ohlcv(
        self,
        ticker:   str,
        interval: str,
        from_dt:  datetime,
        to_dt:    datetime,
    ) -> OHLCVDto:
        self._ensure_connected()

        request = market_pb2.OHLCVRequest(
            ticker   = ticker,
            from_dt  = from_dt.isoformat(),
            to_dt    = to_dt.isoformat(),
            interval = interval,
        )

        try:
            response: market_pb2.OHLCVResponse = await self._stub.GetOHLCV(request)
        except grpc.aio.AioRpcError as exc:
            logger.error("gRPC GetOHLCV failed: %s | ticker=%s", exc.details(), ticker)
            raise GrpcClientError(f"GetOHLCV failed for {ticker}: {exc.details()}") from exc

        bars = tuple(self._parse_bar(b) for b in response.bars)
        return OHLCVDto(ticker=response.ticker, interval=response.interval, bars=bars)

    async def get_last_price(self, ticker: str) -> Decimal:
        self._ensure_connected()

        request = market_pb2.LastPriceRequest(ticker=ticker)

        try:
            response: market_pb2.LastPriceResponse = await self._stub.GetLastPrice(request)
        except grpc.aio.AioRpcError as exc:
            logger.error("gRPC GetLastPrice failed: %s | ticker=%s", exc.details(), ticker)
            raise GrpcClientError(f"GetLastPrice failed for {ticker}: {exc.details()}") from exc

        return Decimal(response.price)

    def _ensure_connected(self) -> None:
        if self._stub is None:
            raise RuntimeError(
                "MarketServiceClient is not connected. "
                "Use it as: async with MarketServiceClient(...) as client: ..."
            )

    @staticmethod
    def _parse_bar(bar: market_pb2.PriceBar) -> PriceBarDto:
        return PriceBarDto(
            time   = datetime.fromisoformat(bar.time).replace(tzinfo=timezone.utc),
            ticker = bar.ticker,
            open   = Decimal(bar.open)  if bar.open  else None,
            high   = Decimal(bar.high)  if bar.high  else None,
            low    = Decimal(bar.low)   if bar.low   else None,
            close  = Decimal(bar.close),
            volume = bar.volume         if bar.volume else None,
        )