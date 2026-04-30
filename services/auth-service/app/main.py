from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.infrastructure.cache.redis_client import get_redis, close_redis
from app.infrastructure.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await get_redis()
    yield
    # shutdown
    await close_redis()
    await engine.dispose()

app = FastAPI(
    root_path='/auth-service',
    version='0.1.0',
    title='Authentication Service',
    lifespan=lifespan
)

Instrumentator().instrument(app).expose(app)

@app.get('/')
async def health():
    return {'status':'health'}