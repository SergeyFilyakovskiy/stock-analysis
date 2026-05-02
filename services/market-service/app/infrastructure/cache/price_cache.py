from decimal import Decimal
from typing import Optional

from redis.asyncio import Redis


class PriceCache:

    KEY_PREFIX = "price"

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, ticker: str) -> str:
        return f"{self.KEY_PREFIX}:{ticker.upper()}"

    async def get(self, ticker: str) -> Optional[Decimal]:
        value = await self._redis.get(self._key(ticker))
        return Decimal(value) if value is not None else None

    async def set(self, ticker: str, price: Decimal, ttl: int = 60) -> None:
        await self._redis.set(self._key(ticker), str(price), ex=ttl)

    async def delete(self, ticker: str) -> None:
        await self._redis.delete(self._key(ticker))

    async def exists(self, ticker: str) -> bool:
        return bool(await self._redis.exists(self._key(ticker)))