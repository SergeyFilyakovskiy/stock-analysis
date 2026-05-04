from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.schemas.patterns import PatternsResponseSchema, CandlePatternSchema
from app.application.queries.get_patterns import GetPatternsQuery
from app.core.dependencies import CacheDep, MarketClientDep

router = APIRouter()


@router.get(
    "/{ticker}",
    response_model=PatternsResponseSchema,
    summary="Паттерны японских свечей",
)
async def get_patterns(
    ticker:   str,
    cache:    CacheDep,
    client:   MarketClientDep,
    interval: Annotated[str, Query(pattern=r"^(1m|5m|1h|1d)$")] = "1d",
) -> PatternsResponseSchema:
    query    = GetPatternsQuery(cache=cache, client=client)
    patterns = await query.execute(ticker=ticker.upper(), interval=interval)

    return PatternsResponseSchema(
        ticker   = ticker.upper(),
        interval = interval,
        patterns = [CandlePatternSchema.model_validate(p) for p in patterns],
    )