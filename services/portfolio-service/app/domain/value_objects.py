from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Ticker:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Ticker cannot be empty")
        object.__setattr__(self, "value", self.value.upper().strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError(f"Money amount cannot be negative: {self.amount}")
        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Invalid currency code: {self.currency}")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add Money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: Decimal) -> "Money":
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class Quantity:
    value: Decimal

    def __post_init__(self) -> None:
        if self.value < Decimal("0"):
            raise ValueError(f"Quantity cannot be negative: {self.value}")

    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value)

    def __sub__(self, other: "Quantity") -> "Quantity":
        result = self.value - other.value
        if result < Decimal("0"):
            raise ValueError("Quantity cannot go below zero")
        return Quantity(result)

    def is_zero(self) -> bool:
        return self.value == Decimal("0")