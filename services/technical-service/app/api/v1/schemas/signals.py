from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.value_objects import SignalType


class SignalResponseSchema(BaseModel):
    ticker:     str
    signal:     SignalType
    confidence: float = Field(ge=0.0, le=1.0)
    breakdown:  dict[str, str]   # {"rsi": "BUY", "macd": "SELL", ...}
    timestamp:  datetime