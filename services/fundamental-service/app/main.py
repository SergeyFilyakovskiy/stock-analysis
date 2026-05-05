from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.routers import api_router
from app.core.config import settings
from app.infrastructure.cache.redis_client import close_redis, get_redis
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ───────────────────────────────────────────────────────────────
    redis = await get_redis()

    yield

    # ── shutdown ──────────────────────────────────────────────────────────────
    await close_redis()
    await engine.dispose()


app = FastAPI(
    root_path="/fundamental-service",
    version="1.0.0",
    title=settings.APP_NAME,
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
    return {"status": "healthy", "service": settings.APP_NAME}