from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.value_objects import SignalType


class CandlePatternSchema(BaseModel):
    ticker:      str
    time:        datetime
    pattern:     str
    direction:   SignalType
    description: Optional[str] = None


class PatternsResponseSchema(BaseModel):
    ticker:   str
    interval: str
    patterns: list[CandlePatternSchema]