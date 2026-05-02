# infrastructure/cache/redis_client.py
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

_pool: ConnectionPool | None = None
_redis: Redis | None = None


async def get_redis() -> Redis:
    global _pool, _redis
    if _redis is None:
        _pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=False,
        )
        _redis = Redis(connection_pool=_pool)
    return _redis


async def close_redis() -> None:
    global _pool, _redis
    if _redis:
        await _redis.aclose()
        _redis = None
    if _pool:
        await _pool.aclose()
        _pool = None