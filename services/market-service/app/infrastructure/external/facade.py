from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.entities import PriceBar
from app.domain.exceptions import ProviderUnavailableError
from app.infrastructure.cache.price_cache import PriceCache
from app.infrastructure.external.base import BaseMarketDataProvider


class MarketDataFacade:
    """
    Стратегия: cache → primary → fallback.
    Скрывает два провайдера за единым интерфейсом.
    """

    def __init__(
        self,
        cache:    PriceCache,
        primary:  BaseMarketDataProvider,
        fallback: BaseMarketDataProvider,
    ) -> None:
        self._cache    = cache
        self._primary  = primary
        self._fallback = fallback

    async def get_last_price(self, ticker: str) -> Decimal:
        # 1. Смотрим кэш
        cached = await self._cache.get(ticker)
        if cached is not None:
            return cached

        # 2. Пробуем primary
        try:
            price = await self._primary.get_last_price(ticker)
        except ProviderUnavailableError:
            # 3. Fallback
            price = await self._fallback.get_last_price(ticker)

        # 4. Кладём в кэш
        await self._cache.set(ticker, price, ttl=60)
        return price

    async def get_historical_bars(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        try:
            return await self._primary.get_historical_bars(
                ticker, from_dt, to_dt, interval
            )
        except ProviderUnavailableError:
            return await self._fallback.get_historical_bars(
                ticker, from_dt, to_dt, interval
            )