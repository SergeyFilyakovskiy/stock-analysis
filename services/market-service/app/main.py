from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.routers import api_router
from app.infrastructure.cache.redis_client import get_redis, close_redis
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
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