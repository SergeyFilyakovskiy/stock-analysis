from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.indicators import IndicatorsResponseSchema, IndicatorResultSchema
from app.application.queries.get_indicators import GetIndicatorsQuery
from app.core.dependencies import CacheDep, MarketClientDep
from app.domain.value_objects import IndicatorType

router = APIRouter()


@router.get(
    "/{ticker}",
    response_model=IndicatorsResponseSchema,
    summary="Рассчитать технические индикаторы",
)
async def get_indicators(
    ticker:   str,
    cache:    CacheDep,
    client:   MarketClientDep,
    types:    Annotated[list[IndicatorType], Query()] = list(IndicatorType),
    period:   Annotated[int,  Query(ge=2, le=200)]   = 14,
    interval: Annotated[str,  Query(pattern=r"^(1m|5m|1h|1d)$")] = "1d",
) -> IndicatorsResponseSchema:
    query = GetIndicatorsQuery(cache=cache, client=client)
    dto   = await query.execute(ticker=ticker.upper(), types=types, period=period, interval=interval)

    return IndicatorsResponseSchema(
        ticker   = dto.ticker,
        interval = dto.interval,
        results  = [IndicatorResultSchema.model_validate(r) for r in dto.results],
    )