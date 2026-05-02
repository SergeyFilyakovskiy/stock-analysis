from fastapi import APIRouter
from app.api.v1.schemas.indices import MarketIndexResponse
from app.core.dependencies import ServiceDep

router = APIRouter(prefix="/indices", tags=["indices"])


@router.get("", response_model=list[MarketIndexResponse])
async def get_market_indices(service: ServiceDep):
    indices = await service.get_market_overview()
    return [MarketIndexResponse(**vars(i)) for i in indices]