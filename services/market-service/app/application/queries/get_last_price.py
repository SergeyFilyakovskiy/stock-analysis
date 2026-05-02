from dataclasses import dataclass
from decimal import Decimal

from app.domain.exceptions import TickerNotFoundError
from app.domain.interfaces import IMarketRepository
from app.infrastructure.cache.price_cache import PriceCache
from app.infrastructure.external.facade import MarketDataFacade


@dataclass(frozen=True)
class GetLastPriceQuery:
    ticker: str


class GetLastPriceHandler:

    def __init__(
        self,
        repo:   IMarketRepository,
        cache:  PriceCache,
        facade: MarketDataFacade,
    ) -> None:
        self._repo   = repo
        self._cache  = cache
        self._facade = facade

    async def handle(self, query: GetLastPriceQuery) -> Decimal:
        ticker = query.ticker.upper()

        # 1. Проверяем что тикер существует
        security = await self._repo.get_security(ticker)
        if not security:
            raise TickerNotFoundError(ticker)

        # 2. Facade: cache → primary → fallback
        return await self._facade.get_last_price(ticker)