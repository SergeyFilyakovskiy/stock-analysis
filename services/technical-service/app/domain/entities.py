from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.value_objects import SignalType, IndicatorType


@dataclass(frozen=True)
class IndicatorConfig:
    """Конфигурация одного индикатора: тип + произвольные параметры."""
    type:   IndicatorType
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class IndicatorResult:
    """Результат расчёта одного значения индикатора."""
    ticker:    str
    time:      datetime
    indicator: IndicatorType
    value:     Decimal
    signal:    SignalType


@dataclass(frozen=True)
class CandlePattern:
    """Найденный паттерн японских свечей."""
    ticker:      str
    time:        datetime
    pattern:     str
    direction:   SignalType
    description: Optional[str] = None