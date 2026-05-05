from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.companies import ScreenerResultSchema, FinancialMetricsSchema
from app.application.queries.run_screener import RunScreenerHandler, ScreenerQuery
from app.core.dependencies import get_screener_handler

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("", response_model=ScreenerResultSchema)
async def run_screener(
    pe_max: Optional[float] = Query(None, ge=0),
    pe_min: Optional[float] = Query(None, ge=0),
    roe_min: Optional[float] = Query(None),
    ev_ebitda_max: Optional[float] = Query(None, ge=0),
    debt_equity_max: Optional[float] = Query(None, ge=0),
    sector: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    handler: RunScreenerHandler = Depends(get_screener_handler),
) -> ScreenerResultSchema:
    result = await handler.handle(ScreenerQuery(
        pe_max=pe_max, pe_min=pe_min, roe_min=roe_min,
        ev_ebitda_max=ev_ebitda_max, debt_equity_max=debt_equity_max,
        sector=sector, limit=limit, offset=offset,
    ))
    return ScreenerResultSchema(
        items=[FinancialMetricsSchema(**{k: v for k, v in m.__dict__.items() if k in FinancialMetricsSchema.model_fields}) for m in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )
