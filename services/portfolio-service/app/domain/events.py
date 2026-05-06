from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TransactionAdded(DomainEvent):
    portfolio_id: UUID = field(default_factory=uuid4)
    ticker: str = ""
    transaction_type: str = ""   # "BUY" | "SELL"
    quantity: Decimal = Decimal("0")
    price: Decimal = Decimal("0")


@dataclass(frozen=True)
class AlertTriggered(DomainEvent):
    alert_id: UUID = field(default_factory=uuid4)
    portfolio_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    ticker: str = ""
    condition: str = ""          # "ABOVE" | "BELOW"
    target_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")


@dataclass(frozen=True)
class PortfolioCreated(DomainEvent):
    portfolio_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    name: str = ""