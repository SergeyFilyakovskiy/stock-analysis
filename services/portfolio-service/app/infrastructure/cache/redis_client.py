from redis.asyncio import Redis

from app.core.config import settings

_market_redis: Redis | None = None
_portfolio_redis: Redis | None = None


async def get_market_redis() -> Redis:
    global _market_redis
    if _market_redis is None:
        _market_redis = Redis.from_url(settings.redis_market_url, decode_responses=True)
    return _market_redis


async def get_portfolio_redis() -> Redis:
    global _portfolio_redis
    if _portfolio_redis is None:
        _portfolio_redis = Redis.from_url(settings.redis_portfolio_url, decode_responses=True)
    return _portfolio_redis


async def close_redis() -> None:
    global _market_redis, _portfolio_redis
    if _market_redis:
        await _market_redis.aclose()
        _market_redis = None
    if _portfolio_redis:
        await _portfolio_redis.aclose()
        _portfolio_redis = None