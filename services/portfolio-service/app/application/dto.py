from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID


@dataclass
class PositionDTO:
    ticker: str
    quantity: Decimal
    avg_price: Decimal
    currency: str


@dataclass
class TransactionDTO:
    id: UUID
    ticker: str
    transaction_type: str
    price: Decimal
    quantity: Decimal
    currency: str
    created_at: datetime


@dataclass
class PortfolioDTO:
    id: UUID
    user_id: UUID
    name: str
    currency: str
    created_at: datetime
    positions: list[PositionDTO]


@dataclass
class AnalyticsPositionDTO:
    ticker: str
    quantity: Decimal
    avg_price: Decimal
    current_price: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal
    weight_pct: Decimal             # доля в портфеле, %


@dataclass
class PortfolioAnalyticsDTO:
    portfolio_id: UUID
    currency: str
    total_cost: Decimal             # сумма avg_price * qty по всем позициям
    total_market_value: Decimal     # сумма current_price * qty
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: Decimal
    positions: list[AnalyticsPositionDTO]


@dataclass
class PriceAlertDTO:
    id: UUID
    portfolio_id: UUID
    ticker: str
    condition: str
    target_price: Decimal
    currency: str
    is_active: bool
    created_at: datetime


@dataclass
class WatchlistItemDTO:
    id: UUID
    ticker: str
    added_at: datetime


@dataclass
class WatchlistDTO:
    id: UUID
    name: str
    user_id: UUID
    created_at: datetime
    items: list[WatchlistItemDTO]