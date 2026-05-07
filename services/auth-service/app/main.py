from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.routers import v1_router
from app.core.config import settings
from app.infrastructure.cache.redis_client import close_redis, get_redis
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    version="0.1.0",
    title="Authentication Service",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret.get_secret_value(),
    https_only=False,
    max_age=300,
)

app.include_router(v1_router)

Instrumentator().instrument(app).expose(app)


@app.get("/")
async def health():
    return {"status": "healthy"}