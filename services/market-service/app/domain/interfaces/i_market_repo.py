from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.entities import Security, PriceBar, Dividend, MarketIndex


class IMarketRepository(ABC):

    @abstractmethod
    async def get_security(self, ticker: str) -> Optional[Security]:
        ...

    @abstractmethod
    async def search_securities(self, query: str) -> list[Security]:
        ...

    @abstractmethod
    async def get_price_history(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[PriceBar]:
        ...

    @abstractmethod
    async def get_ohlcv(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        ...

    @abstractmethod
    async def get_last_price(self, ticker: str) -> Optional[Decimal]:
        ...

    @abstractmethod
    async def save_price_bars(self, bars: list[PriceBar]) -> None:
        ...

    @abstractmethod
    async def get_dividends(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[Dividend]:
        ...

    @abstractmethod
    async def get_market_indices(self) -> list[MarketIndex]:
        ...