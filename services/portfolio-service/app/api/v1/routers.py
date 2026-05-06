from fastapi import APIRouter

from app.api.v1.endpoints.portfolios import router as portfolios_router
from app.api.v1.endpoints.transactions import router as transactions_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.watchlists import router as watchlists_router

api_router = APIRouter(prefix="/api/v1/portfolio")

api_router.include_router(portfolios_router)
api_router.include_router(transactions_router)
api_router.include_router(analytics_router)
api_router.include_router(alerts_router)
api_router.include_router(watchlists_router)