from fastapi import APIRouter

from app.api.v1.endpoints.indicators import router as indicators_router
from app.api.v1.endpoints.signals    import router as signals_router
from app.api.v1.endpoints.patterns   import router as patterns_router

v1_router = APIRouter(prefix="/api/v1/technical")

v1_router.include_router(indicators_router, prefix="/indicators", tags=["indicators"])
v1_router.include_router(signals_router,    prefix="/signals",    tags=["signals"])
v1_router.include_router(patterns_router,   prefix="/patterns",   tags=["patterns"])