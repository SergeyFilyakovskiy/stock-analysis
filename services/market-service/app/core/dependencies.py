from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.commands.ingest_price_data import IngestPriceDataHandler
from app.application.queries.get_dividends import GetDividendsHandler
from app.application.queries.get_last_price import GetLastPriceHandler
from app.application.queries.get_market_overview import GetMarketOverviewHandler
from app.application.queries.get_ohlcv import GetOHLCVHandler
from app.application.queries.search_securities import SearchSecuritiesHandler
from app.application.services.market_data_service import MarketDataService
from app.core.config import settings
from app.infrastructure.cache.price_cache import PriceCache
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.db.repositories.market_repo import MarketRepository
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.external.alpha_vantage import AlphaVantageProvider
from app.infrastructure.external.facade import MarketDataFacade
from app.infrastructure.external.polygon import PolygonProvider
from app.infrastructure.messaging.publisher import MarketEventPublisher


# ─────────────────────────────────────────────
# Инфраструктура
# ─────────────────────────────────────────────


async def get_redis_client() -> Redis:
    return await get_redis()


def get_price_cache(
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> PriceCache:
    return PriceCache(redis)


def get_primary_provider() -> AlphaVantageProvider:
    return AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_KEY.get_secret_value())


def get_fallback_provider() -> PolygonProvider:
    return PolygonProvider(api_key=settings.POLYGON_KEY.get_secret_value())


def get_facade(
    cache:    Annotated[PriceCache,           Depends(get_price_cache)],
    primary:  Annotated[AlphaVantageProvider, Depends(get_primary_provider)],
    fallback: Annotated[PolygonProvider,      Depends(get_fallback_provider)],
) -> MarketDataFacade:
    return MarketDataFacade(cache=cache, primary=primary, fallback=fallback)


def get_publisher() -> MarketEventPublisher:
    return MarketEventPublisher()


def get_repo() -> MarketRepository:
    return MarketRepository(async_session_factory)


# ─────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────

def get_last_price_handler(
    repo:   Annotated[MarketRepository, Depends(get_repo)],
    cache:  Annotated[PriceCache,       Depends(get_price_cache)],
    facade: Annotated[MarketDataFacade, Depends(get_facade)],
) -> GetLastPriceHandler:
    return GetLastPriceHandler(repo=repo, cache=cache, facade=facade)


def get_ohlcv_handler(
    repo: Annotated[MarketRepository, Depends(get_repo)],
) -> GetOHLCVHandler:
    return GetOHLCVHandler(repo=repo)


def get_search_securities_handler(
    repo: Annotated[MarketRepository, Depends(get_repo)],
) -> SearchSecuritiesHandler:
    return SearchSecuritiesHandler(repo=repo)


def get_market_overview_handler(
    repo: Annotated[MarketRepository, Depends(get_repo)],
) -> GetMarketOverviewHandler:
    return GetMarketOverviewHandler(repo=repo)


def get_dividends_handler(
    repo: Annotated[MarketRepository, Depends(get_repo)],
) -> GetDividendsHandler:
    return GetDividendsHandler(repo=repo)


def get_ingest_handler(
    repo:      Annotated[MarketRepository,    Depends(get_repo)],
    facade:    Annotated[MarketDataFacade,    Depends(get_facade)],
    publisher: Annotated[MarketEventPublisher, Depends(get_publisher)],
) -> IngestPriceDataHandler:
    return IngestPriceDataHandler(repo=repo, facade=facade, publisher=publisher)


# ─────────────────────────────────────────────
# Service (финальная зависимость для эндпоинтов)
# ─────────────────────────────────────────────

def get_market_data_service(
    get_last_price:      Annotated[GetLastPriceHandler,      Depends(get_last_price_handler)],
    get_ohlcv:           Annotated[GetOHLCVHandler,          Depends(get_ohlcv_handler)],
    search_securities:   Annotated[SearchSecuritiesHandler,  Depends(get_search_securities_handler)],
    get_market_overview: Annotated[GetMarketOverviewHandler, Depends(get_market_overview_handler)],
    get_dividends:       Annotated[GetDividendsHandler,      Depends(get_dividends_handler)],
    ingest:              Annotated[IngestPriceDataHandler,   Depends(get_ingest_handler)],
) -> MarketDataService:
    return MarketDataService(
        get_last_price_handler=get_last_price,
        get_ohlcv_handler=get_ohlcv,
        search_securities_handler=search_securities,
        get_market_overview_handler=get_market_overview,
        get_dividends_handler=get_dividends,
        ingest_handler=ingest,
    )


# Удобный алиас для эндпоинтов
ServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]


#GRPC
from app.grpc.servicer import MarketServicer


def get_grpc_servicer(
    get_ohlcv:      Annotated[GetOHLCVHandler,      Depends(get_ohlcv_handler)],
    get_last_price: Annotated[GetLastPriceHandler,   Depends(get_last_price_handler)],
) -> MarketServicer:
    return MarketServicer(
        get_ohlcv_handler=get_ohlcv,
        get_last_price_handler=get_last_price,
    )