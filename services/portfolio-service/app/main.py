import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.routers import api_router
from app.core.config import settings
from app.infrastructure.cache.redis_client import close_redis, get_market_redis, get_portfolio_redis
from app.infrastructure.db.session import engine
from app.infrastructure.messaging.consumer import consume_price_events
from app.workers.alert_checker import check_alerts
from app.workers.outbox_relay import run_outbox_relay


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await get_market_redis()
    await get_portfolio_redis()

    loop = asyncio.get_event_loop()
    consumer_task = loop.create_task(consume_price_events(check_alerts))
    relay_task = loop.create_task(run_outbox_relay())

    yield

    # shutdown
    consumer_task.cancel()
    relay_task.cancel()
    await close_redis()
    await engine.dispose()


app = FastAPI(
    root_path="/portfolio-service",
    version="1.0.0",
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

Instrumentator().instrument(app).expose(app)


@app.get("/", tags=["health"])
async def health():
    return {"status": "healthy", "service": settings.app_name}