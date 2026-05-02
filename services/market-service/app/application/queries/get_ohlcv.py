from dataclasses import dataclass
from datetime import datetime

from app.application.dto import OHLCVDto, PriceBarDto
from app.domain.entities import PriceBar
from app.domain.exceptions import TickerNotFoundError
from app.domain.interfaces import IMarketRepository


@dataclass(frozen=True)
class GetOHLCVQuery:
    ticker:   str
    from_dt:  datetime
    to_dt:    datetime
    interval: str


def _to_dto(bar: PriceBar) -> PriceBarDto:
    return PriceBarDto(
        time=bar.time,
        ticker=bar.ticker,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        source=bar.source,
    )


class GetOHLCVHandler:

    def __init__(self, repo: IMarketRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetOHLCVQuery) -> OHLCVDto:
        ticker = query.ticker.upper()

        security = await self._repo.get_security(ticker)
        if not security:
            raise TickerNotFoundError(ticker)

        bars = await self._repo.get_ohlcv(
            ticker=ticker,
            from_dt=query.from_dt,
            to_dt=query.to_dt,
            interval=query.interval,
        )

        return OHLCVDto(
            ticker=ticker,
            interval=query.interval,
            bars=tuple(_to_dto(b) for b in bars),
        )