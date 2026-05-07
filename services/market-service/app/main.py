from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.routers import api_router
from app.core.config import settings
from app.infrastructure.cache.price_cache import PriceCache
from app.infrastructure.cache.redis_client import get_redis, close_redis
from app.infrastructure.db.session import engine, async_session_factory
from app.infrastructure.db.repositories.market_repo import MarketRepository
from app.grpc import create_grpc_server
from app.grpc.servicer import MarketServicer


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = await get_redis()
    cache = PriceCache(redis)

    from app.infrastructure.external.alpha_vantage import AlphaVantageProvider
    from app.infrastructure.external.polygon import PolygonProvider
    from app.infrastructure.external.facade import MarketDataFacade
    from app.application.queries.get_ohlcv import GetOHLCVHandler
    from app.application.queries.get_last_price import GetLastPriceHandler

    primary  = AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_KEY.get_secret_value())
    fallback = PolygonProvider(api_key=settings.POLYGON_KEY.get_secret_value())
    facade   = MarketDataFacade(cache=cache, primary=primary, fallback=fallback)

    repo = MarketRepository(session_factory=async_session_factory)  # ← per-call sessions

    servicer = MarketServicer(
        get_ohlcv_handler=GetOHLCVHandler(repo=repo),
        get_last_price_handler=GetLastPriceHandler(
            repo=repo,
            cache=cache,
            facade=facade,
        ),
    )

    grpc_server = await create_grpc_server(servicer)
    await grpc_server.start()

    yield

    await grpc_server.stop(grace=5)
    await close_redis()
    await engine.dispose()


app = FastAPI(
    root_path="/market-service",
    version="1.0.0",
    title="Market Data Service",
    lifespan=lifespan,
)

app.include_router(api_router)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def health():
    return {"status": "healthy"}