from fastapi import APIRouter, HTTPException, Query
from app.api.v1.schemas.securities import SecurityResponse, SecuritiesListResponse
from app.core.dependencies import ServiceDep
from app.domain.exceptions import TickerNotFoundError

router = APIRouter(prefix="/securities", tags=["securities"])


@router.get("", response_model=SecuritiesListResponse)
async def search_securities(
    service: ServiceDep,
    q: str = Query(default="", description="Поиск по названию"),
):
    items = await service.search_securities(q)
    return SecuritiesListResponse(
        items=[SecurityResponse(**vars(i)) for i in items],
        total=len(items),
    )


@router.get("/{ticker}", response_model=SecurityResponse)
async def get_security(ticker: str, service: ServiceDep):
    try:
        items = await service.search_securities(ticker)
        match = next((i for i in items if i.ticker == ticker.upper()), None)
        if not match:
            raise TickerNotFoundError(ticker)
        return SecurityResponse(**vars(match))
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")


@router.get("/{ticker}/price", response_model=dict)
async def get_last_price(ticker: str, service: ServiceDep):
    try:
        price = await service.get_last_price(ticker)
        return {"ticker": ticker.upper(), "price": str(price)}
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")