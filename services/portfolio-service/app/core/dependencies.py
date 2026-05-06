from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import AsyncSessionFactory
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.cache.redis_client import get_market_redis, get_portfolio_redis
from app.infrastructure.cache.pnl_cache import PnlCache
from app.grpc_client.market_client import MarketGrpcClient


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    async with AsyncSessionFactory() as session:
        yield UnitOfWork(session)


async def get_pnl_cache() -> PnlCache:
    redis = await get_portfolio_redis()
    return PnlCache(redis)


async def get_market_client() -> MarketGrpcClient:
    return MarketGrpcClient()


def get_current_user_id(
    x_user_id: str | None = Header(default=None),
) -> UUID:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid X-User-Id format")