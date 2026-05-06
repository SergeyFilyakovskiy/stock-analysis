from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PositionResponse(BaseModel):
    ticker: str
    quantity: Decimal
    avg_price: Decimal
    currency: str


class PortfolioCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PortfolioResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    currency: str
    created_at: datetime
    positions: list[PositionResponse] = []

    model_config = {"from_attributes": True}


class PortfolioListResponse(BaseModel):
    id: UUID
    name: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}