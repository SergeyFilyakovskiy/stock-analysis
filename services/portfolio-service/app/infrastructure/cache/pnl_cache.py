import json
from decimal import Decimal
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings


class PnlCache:
    """
    Кэш P&L по portfolio_id.
    TTL=30s, явная инвалидация при add_transaction.
    Цены тикеров читаются из redis_market_db (market-service).
    """

    _PNL_PREFIX = "pnl:"
    _PRICE_PREFIX = "price:"           # ключи от market-service

    def __init__(self, portfolio_redis: Redis, market_redis: Redis | None = None) -> None:
        self._portfolio_redis = portfolio_redis
        self._market_redis = market_redis

    async def get(self, portfolio_id: UUID) -> dict | None:
        raw = await self._portfolio_redis.get(f"{self._PNL_PREFIX}{portfolio_id}")
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, portfolio_id: UUID, data: dict) -> None:
        await self._portfolio_redis.setex(
            f"{self._PNL_PREFIX}{portfolio_id}",
            settings.pnl_cache_ttl,
            json.dumps(data, default=str),
        )

    async def invalidate(self, portfolio_id: UUID) -> None:
        await self._portfolio_redis.delete(f"{self._PNL_PREFIX}{portfolio_id}")

    async def get_price(self, ticker: str) -> Decimal | None:
        """Читает последнюю цену из redis_market_db (записывает market-service)."""
        if self._market_redis is None:
            return None
        raw = await self._market_redis.get(f"{self._PRICE_PREFIX}{ticker.upper()}")
        if raw is None:
            return None
        try:
            return Decimal(raw)
        except Exception:
            return None

    async def get_prices_batch(self, tickers: list[str]) -> dict[str, Decimal]:
        if not tickers or self._market_redis is None:
            return {}
        keys = [f"{self._PRICE_PREFIX}{t.upper()}" for t in tickers]
        values = await self._market_redis.mget(*keys)
        result: dict[str, Decimal] = {}
        for ticker, raw in zip(tickers, values):
            if raw is not None:
                try:
                    result[ticker.upper()] = Decimal(raw)
                except Exception:
                    pass
        return result