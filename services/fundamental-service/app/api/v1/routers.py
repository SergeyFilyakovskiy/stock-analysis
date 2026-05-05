from fastapi import APIRouter

from app.api.v1.endpoints.companies import router as companies_router
from app.api.v1.endpoints.screener import router as screener_router
from app.api.v1.endpoints.compare import router as compare_router


api_router = APIRouter(prefix="/api/v1/fundamental")
api_router.include_router(companies_router)
api_router.include_router(screener_router)
api_router.include_router(compare_router)

