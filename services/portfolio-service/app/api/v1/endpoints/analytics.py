from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas.analytics import PortfolioAnalyticsResponse, AnalyticsPositionResponse
from app.application.queries.get_portfolio_analytics import (
    GetPortfolioAnalyticsHandler,
    GetPortfolioAnalyticsQuery,
)
from app.core.dependencies import get_current_user_id, get_pnl_cache, get_session
from app.domain.exceptions import PortfolioAccessDenied, PortfolioNotFound
from app.infrastructure.cache.pnl_cache import PnlCache

router = APIRouter(prefix="/portfolios", tags=["analytics"])


@router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session=Depends(get_session),
    pnl_cache: PnlCache = Depends(get_pnl_cache),
):
    try:
        handler = GetPortfolioAnalyticsHandler(session, pnl_cache)
        dto = await handler.handle(
            GetPortfolioAnalyticsQuery(portfolio_id=portfolio_id, user_id=user_id)
        )
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return PortfolioAnalyticsResponse(
        portfolio_id=dto.portfolio_id,
        currency=dto.currency,
        total_cost=dto.total_cost,
        total_market_value=dto.total_market_value,
        total_unrealized_pnl=dto.total_unrealized_pnl,
        total_unrealized_pnl_pct=dto.total_unrealized_pnl_pct,
        positions=[
            AnalyticsPositionResponse(
                ticker=p.ticker,
                quantity=p.quantity,
                avg_price=p.avg_price,
                current_price=p.current_price,
                market_value=p.market_value,
                unrealized_pnl=p.unrealized_pnl,
                weight_pct=p.weight_pct,
            )
            for p in dto.positions
        ],
    )