from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class PriceBarResponse(BaseModel):
    time:   datetime
    ticker: str
    open:   Optional[Decimal]
    high:   Optional[Decimal]
    low:    Optional[Decimal]
    close:  Decimal
    volume: Optional[int]
    source: Optional[str]

    model_config = {"from_attributes": True}


class OHLCVResponse(BaseModel):
    ticker:   str
    interval: str
    bars:     list[PriceBarResponse]


class LastPriceResponse(BaseModel):
    ticker: str
    price:  Decimal