from fastapi import APIRouter
from app.api.v1.endpoints import securities, prices, dividends, indices, stream

api_router = APIRouter(prefix="/api/v1/market")

api_router.include_router(securities.router)
api_router.include_router(prices.router)
api_router.include_router(dividends.router)
api_router.include_router(indices.router)
api_router.include_router(stream.router)