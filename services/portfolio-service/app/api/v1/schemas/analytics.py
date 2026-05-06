from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AnalyticsPositionResponse(BaseModel):
    ticker: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal
    weight_pct: Decimal


class PortfolioAnalyticsResponse(BaseModel):
    portfolio_id: UUID
    currency: str
    total_cost: Decimal
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: Decimal
    positions: list[AnalyticsPositionResponse]