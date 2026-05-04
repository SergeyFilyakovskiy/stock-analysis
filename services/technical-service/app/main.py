from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.routers import v1_router
from app.core.config import settings
from app.infrastructure.cache.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # nothing to init — Redis открывается лениво при первом запросе (синглтон)
    yield
    await close_redis()


app = FastAPI(
    root_path="/technical-analysis-service",
    version="1.0.0",
    title="Technical Analysis Service",
    lifespan=lifespan,
)

app.include_router(v1_router)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    return {"status": "healthy"}
