from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities import Security, PriceBar, Dividend, MarketIndex
from app.domain.interfaces import IMarketRepository
from app.infrastructure.db.models import (
    SecurityModel,
    PriceHistoryModel,
    DividendModel,
    MarketIndexModel,
)

_INTERVAL_VIEW_MAP = {
    "1m":  "ohlcv_1m",
    "5m":  "ohlcv_1m",
    "15m": "ohlcv_1m",
    "30m": "ohlcv_1m",
    "1h":  "ohlcv_1h",
    "4h":  "ohlcv_1h",
    "1d":  "ohlcv_1d",
    "1w":  "ohlcv_1d",
}


def _to_security(m: SecurityModel) -> Security:
    return Security(
        ticker=m.ticker,
        name=m.name,
        exchange=m.exchange,
        sector=m.sector,
        is_active=m.is_active,
    )


def _to_price_bar(m: PriceHistoryModel) -> PriceBar:
    return PriceBar(
        time=m.time,
        ticker=m.ticker,
        open=m.open,
        high=m.high,
        low=m.low,
        close=m.close,
        volume=m.volume,
        source=m.source,
    )


def _to_dividend(m: DividendModel) -> Dividend:
    return Dividend(
        ticker=m.ticker,
        ex_date=m.ex_date,
        pay_date=m.pay_date,
        amount=m.amount,
        currency=m.currency,
    )


def _to_market_index(m: MarketIndexModel) -> MarketIndex:
    return MarketIndex(
        index_code=m.index_code,
        name=m.name,
        description=m.description,
        is_active=m.is_active,
    )


class MarketRepository(IMarketRepository):

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    # ── helpers ──────────────────────────────────────────────────────────

    async def get_security(self, ticker: str) -> Optional[Security]:
        async with self._session_factory() as session:
            result = await session.get(SecurityModel, ticker.upper())
            return _to_security(result) if result else None

    async def search_securities(self, query: str) -> list[Security]:
        async with self._session_factory() as session:
            stmt = select(SecurityModel).where(
                SecurityModel.is_active.is_(True),
                or_(
                    SecurityModel.ticker.ilike(f"%{query}%"),
                    SecurityModel.name.ilike(f"%{query}%"),
                ),
            )
            rows = await session.scalars(stmt)
            return [_to_security(r) for r in rows]

    async def get_price_history(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[PriceBar]:
        async with self._session_factory() as session:
            stmt = (
                select(PriceHistoryModel)
                .where(
                    and_(
                        PriceHistoryModel.ticker == ticker.upper(),
                        PriceHistoryModel.time >= from_dt,
                        PriceHistoryModel.time <= to_dt,
                    )
                )
                .order_by(PriceHistoryModel.time)
            )
            rows = await session.scalars(stmt)
            return [_to_price_bar(r) for r in rows]

    async def get_ohlcv(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        view = _INTERVAL_VIEW_MAP.get(interval, "ohlcv_1m")
        stmt = f"""
            SELECT bucket AS time, ticker, open, high, low, close, volume
            FROM {view}
            WHERE ticker = :ticker
              AND bucket >= :from_dt
              AND bucket <= :to_dt
            ORDER BY bucket
        """
        async with self._session_factory() as session:
            rows = await session.execute(
                text(stmt),
                {"ticker": ticker.upper(), "from_dt": from_dt, "to_dt": to_dt},
            )
            return [
                PriceBar(
                    time=row.time,
                    ticker=row.ticker,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    volume=row.volume,
                )
                for row in rows
            ]

    async def get_last_price(self, ticker: str) -> Optional[Decimal]:
        async with self._session_factory() as session:
            stmt = (
                select(PriceHistoryModel.close)
                .where(PriceHistoryModel.ticker == ticker.upper())
                .order_by(PriceHistoryModel.time.desc())
                .limit(1)
            )
            return await session.scalar(stmt)

    async def save_price_bars(self, bars: list[PriceBar]) -> None:
        async with self._session_factory() as session:
            for bar in bars:
                model = PriceHistoryModel(
                    time=bar.time,
                    ticker=bar.ticker,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    source=bar.source,
                )
                await session.merge(model)
            await session.commit()

    async def get_dividends(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[Dividend]:
        filters = [DividendModel.ticker == ticker.upper()]
        if from_date:
            filters.append(DividendModel.ex_date >= from_date)
        if to_date:
            filters.append(DividendModel.ex_date <= to_date)

        stmt = (
            select(DividendModel)
            .where(and_(*filters))
            .order_by(DividendModel.ex_date.desc())
        )
        async with self._session_factory() as session:
            rows = await session.scalars(stmt)
            return [_to_dividend(r) for r in rows]

    async def get_market_indices(self) -> list[MarketIndex]:
        async with self._session_factory() as session:
            stmt = select(MarketIndexModel).where(MarketIndexModel.is_active.is_(True))
            rows = await session.scalars(stmt)
            return [_to_market_index(r) for r in rows]