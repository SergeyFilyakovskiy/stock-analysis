from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Ticker:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.isalpha():
            raise ValueError(f"Invalid ticker: '{self.value}'")
        object.__setattr__(self, "value", self.value.upper())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Price:
    amount: Decimal

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price cannot be negative")

    def __str__(self) -> str:
        return str(self.amount)


@dataclass(frozen=True)
class OHLCVInterval:
    """Допустимые интервалы свечей."""
    value: str

    SUPPORTED = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}

    def __post_init__(self):
        if self.value not in self.SUPPORTED:
            from app.domain.exceptions import InvalidIntervalError
            raise InvalidIntervalError(self.value)

    def __str__(self) -> str:
        return self.value