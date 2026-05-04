from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domain.value_objects import SignalType, IndicatorType


class IndicatorResultSchema(BaseModel):
    ticker:    str
    time:      datetime
    indicator: IndicatorType
    value:     Decimal
    signal:    SignalType

    model_config = {"from_attributes": True}


class IndicatorsResponseSchema(BaseModel):
    ticker:   str
    interval: str
    results:  list[IndicatorResultSchema]