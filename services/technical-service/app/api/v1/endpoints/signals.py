from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.signals import SignalResponseSchema
from app.application.queries.get_signals import GetSignalsQuery
from app.core.dependencies import CacheDep, MarketClientDep

router = APIRouter()


@router.get(
    "/{ticker}",
    response_model=SignalResponseSchema,
    summary="Агрегированный торговый сигнал",
)
async def get_signal(
    ticker:   str,
    cache:    CacheDep,
    client:   MarketClientDep,
    interval: Annotated[str, Query(pattern=r"^(1m|5m|1h|1d)$")] = "1d",
) -> SignalResponseSchema:
    query = GetSignalsQuery(cache=cache, client=client)
    dto   = await query.execute(ticker=ticker.upper(), interval=interval)

    return SignalResponseSchema(
        ticker     = dto.ticker,
        signal     = dto.signal,
        confidence = dto.confidence,
        breakdown  = dto.breakdown,
        timestamp  = dto.timestamp,
    )