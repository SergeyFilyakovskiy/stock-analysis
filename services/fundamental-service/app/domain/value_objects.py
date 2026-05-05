from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass(frozen=True)
class Ticker:
    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[A-Z]{1,5}$", self.value):
            raise ValueError(f"Invalid ticker: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Period:
    """Формат: 2024Q1, 2024Q2, 2024FY"""
    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^\d{4}(Q[1-4]|FY)$", self.value):
            raise ValueError(f"Invalid period: {self.value!r}")

    @property
    def year(self) -> int:
        return int(self.value[:4])

    @property
    def is_annual(self) -> bool:
        return self.value.endswith("FY")

    @property
    def quarter(self) -> int | None:
        if self.is_annual:
            return None
        return int(self.value[5])

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MoneyAmount:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if len(self.currency) != 3:
            raise ValueError(f"Invalid currency code: {self.currency!r}")

    def __add__(self, other: "MoneyAmount") -> "MoneyAmount":
        if self.currency != other.currency:
            raise ValueError("Cannot add amounts in different currencies")
        return MoneyAmount(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


@dataclass(frozen=True)
class ValuationResult:
    ticker: str
    model_name: str
    estimated_value: Decimal
    current_price: Decimal
    confidence_score: float   # 0.0 – 1.0
    upside_pct: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0 and 1")

    @property
    def is_undervalued(self) -> bool:
        return self.estimated_value > self.current_price

    @property
    def upside(self) -> Decimal:
        if self.current_price == 0:
            return Decimal("0")
        return ((self.estimated_value - self.current_price)
                / self.current_price * 100).quantize(Decimal("0.01"))