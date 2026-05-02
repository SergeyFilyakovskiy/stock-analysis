from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.api.v1.schemas.dividends import DividendResponse
from app.core.dependencies import ServiceDep
from app.domain.exceptions import TickerNotFoundError

router = APIRouter(prefix="/securities", tags=["dividends"])


@router.get("/{ticker}/dividends", response_model=list[DividendResponse])
async def get_dividends(
    ticker:    str,
    service:   ServiceDep,
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date:   Optional[str] = Query(default=None, alias="to"),
):
    try:
        dividends = await service.get_dividends(
            ticker=ticker,
            from_date=from_date,
            to_date=to_date,
        )
        return [DividendResponse(**vars(d)) for d in dividends]
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")