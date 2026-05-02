from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional


class DividendResponse(BaseModel):
    ticker:   str
    ex_date:  date
    pay_date: Optional[date]
    amount:   Decimal
    currency: str

    model_config = {"from_attributes": True}