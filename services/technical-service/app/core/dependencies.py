from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings
from app.grpc.client import MarketServiceClient
from app.infrastructure.cache.indicator_cache import IndicatorCache
from app.infrastructure.cache.redis_client import get_redis


# ── Redis ─────────────────────────────────────────────────────────────────────

RedisDep = Annotated[Redis, Depends(get_redis)]


# ── IndicatorCache ────────────────────────────────────────────────────────────

async def get_indicator_cache(redis: RedisDep) -> IndicatorCache:
    return IndicatorCache(redis=redis, ttl=settings.cache_ttl)


CacheDep = Annotated[IndicatorCache, Depends(get_indicator_cache)]


# ── MarketServiceClient ───────────────────────────────────────────────────────

async def get_market_client() -> MarketServiceClient:
    """
    Возвращает клиент без открытия канала —
    канал открывается внутри каждого use-case через async with.
    """
    return MarketServiceClient(target=settings.grpc_market_target)


MarketClientDep = Annotated[MarketServiceClient, Depends(get_market_client)]