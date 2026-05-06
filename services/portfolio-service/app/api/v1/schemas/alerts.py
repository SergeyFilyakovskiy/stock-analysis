from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AlertCreateRequest(BaseModel):
    portfolio_id: UUID
    ticker: str = Field(..., min_length=1, max_length=20)
    condition: Literal["ABOVE", "BELOW"]
    target_price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AlertResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    ticker: str
    condition: str
    target_price: Decimal
    currency: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}