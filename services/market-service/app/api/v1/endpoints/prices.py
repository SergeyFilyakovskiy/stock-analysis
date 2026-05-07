from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.api.v1.schemas.prices import OHLCVResponse, PriceBarResponse
from app.core.dependencies import ServiceDep
from app.domain.exceptions import TickerNotFoundError, InvalidIntervalError

router = APIRouter(prefix="/securities", tags=["prices"])


@router.get("/{ticker}/history", response_model=list[PriceBarResponse])
async def get_price_history(
    ticker:   str,
    service:  ServiceDep,
    from_dt:  datetime = Query(..., alias="from"),
    to_dt:    datetime = Query(..., alias="to"),
    interval: str      = Query(default="1m"),
):
    try:
        result = await service.get_ohlcv(
            ticker=ticker,
            from_dt=from_dt,
            to_dt=to_dt,
            interval=interval,
        )
        return [PriceBarResponse(**vars(b)) for b in result.bars]
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    except InvalidIntervalError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ticker}/ohlcv", response_model=OHLCVResponse)
async def get_ohlcv(
    ticker:   str,
    service:  ServiceDep,
    from_dt:  datetime = Query(..., alias="from"),
    to_dt:    datetime = Query(..., alias="to"),
    interval: str      = Query(default="1h"),
):
    try:
        result = await service.get_ohlcv(
            ticker=ticker,
            from_dt=from_dt,
            to_dt=to_dt,
            interval=interval,
        )
        return OHLCVResponse(
            ticker=result.ticker,
            interval=result.interval,
            bars=[PriceBarResponse(**vars(b)) for b in result.bars],
        )
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    except InvalidIntervalError as e:
        raise HTTPException(status_code=400, detail=str(e))