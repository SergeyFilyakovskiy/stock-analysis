from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.value_objects import SignalType, IndicatorType


@dataclass(frozen=True)
class IndicatorResultDto:
    """Одно значение индикатора — ложится в API-ответ."""
    ticker:    str
    time:      datetime
    indicator: IndicatorType
    value:     Decimal
    signal:    SignalType


@dataclass(frozen=True)
class IndicatorsResponseDto:
    """Ответ на запрос нескольких индикаторов для одного тикера."""
    ticker:   str
    interval: str
    results:  tuple[IndicatorResultDto, ...]


@dataclass(frozen=True)
class SignalDto:
    """Итоговый торговый сигнал по тикеру на основе набора индикаторов."""
    ticker:     str
    signal:     SignalType
    confidence: float              # 0.0 – 1.0, доля индикаторов согласных с сигналом
    breakdown:  dict[str, str]     # {"rsi": "BUY", "macd": "SELL", ...}
    timestamp:  datetime


@dataclass(frozen=True)
class CandlePatternDto:
    """Найденный паттерн японских свечей."""
    ticker:      str
    time:        datetime
    pattern:     str
    direction:   SignalType
    description: Optional[str] = None
