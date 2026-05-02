import asyncio
from datetime import datetime, timedelta, timezone

from celery import current_app


@current_app.task(name="workers.fetch_all_prices") # type: ignore
def fetch_all_prices() -> None:
    asyncio.run(_fetch_all_prices())


async def _fetch_all_prices() -> None:
    from sqlalchemy import select

    from app.core.config import settings
    from app.infrastructure.cache.price_cache import PriceCache
    from app.infrastructure.cache.redis_client import get_redis
    from app.infrastructure.db.models import SecurityModel
    from app.infrastructure.db.session import async_session_factory
    from app.infrastructure.db.repositories.market_repo import MarketRepository
    from app.infrastructure.external.alpha_vantage import AlphaVantageProvider
    from app.infrastructure.external.facade import MarketDataFacade
    from app.infrastructure.external.polygon import PolygonProvider
    from app.infrastructure.messaging.publisher import MarketEventPublisher
    from app.application.commands.ingest_price_data import (
        IngestPriceDataCommand,
        IngestPriceDataHandler,
    )

    redis     = await get_redis()
    cache     = PriceCache(redis)
    primary   = AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_KEY.get_secret_value())
    fallback  = PolygonProvider(api_key=settings.POLYGON_KEY.get_secret_value())
    facade    = MarketDataFacade(cache=cache, primary=primary, fallback=fallback)
    publisher = MarketEventPublisher()

    await publisher.connect()

    try:
        async with async_session_factory() as session:
            repo    = MarketRepository(session)
            handler = IngestPriceDataHandler(
                repo=repo,
                facade=facade,
                publisher=publisher,
            )

            tickers = (await session.scalars(
                select(SecurityModel.ticker)
                .where(SecurityModel.is_active.is_(True))
            )).all()

            to_dt   = datetime.now(timezone.utc)
            from_dt = to_dt - timedelta(minutes=5)

            for ticker in tickers:
                try:
                    await handler.handle(IngestPriceDataCommand(
                        ticker=ticker,
                        from_dt=from_dt,
                        to_dt=to_dt,
                        interval="1m",
                    ))
                except Exception:
                    continue
    finally:
        await publisher.close()