from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.domain.entities import PriceBar


class BaseMarketDataProvider(ABC):
    """
    Базовый класс для внешних провайдеров рыночных данных.
    Реализует IMarketDataProvider + хранит имя провайдера.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def get_last_price(self, ticker: str) -> Decimal: ...

    @abstractmethod
    async def get_historical_bars(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]: ...