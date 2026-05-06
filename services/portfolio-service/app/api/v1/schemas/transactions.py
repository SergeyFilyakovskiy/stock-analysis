from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreateRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    transaction_type: Literal["BUY", "SELL"]
    price: Decimal = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class TransactionResponse(BaseModel):
    id: UUID
    ticker: str
    transaction_type: str
    price: Decimal
    quantity: Decimal
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int