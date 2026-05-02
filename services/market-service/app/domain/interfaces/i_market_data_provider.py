from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.entities import PriceBar


class IMarketDataProvider(ABC):

    @abstractmethod
    async def get_last_price(self, ticker: str) -> Decimal:
        """Получить последнюю цену. Бросает ProviderUnavailableError при сбое."""
        ...

    @abstractmethod
    async def get_historical_bars(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        """Получить исторические свечи."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя провайдера для логов и ошибок."""
        ...