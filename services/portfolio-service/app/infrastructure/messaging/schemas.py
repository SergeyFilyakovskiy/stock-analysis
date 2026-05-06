from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class PriceUpdatedEvent:
    event_id: str
    event: str
    ticker: str
    price: Decimal
    timestamp: datetime
    source: str

    @classmethod
    def from_dict(cls, data: dict) -> "PriceUpdatedEvent":
        return cls(
            event_id=data["event_id"],
            event=data["event"],
            ticker=data["ticker"],
            price=Decimal(data["price"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source", ""),
        )


@dataclass
class AlertTriggeredMessage:
    event_id: str
    alert_id: str
    portfolio_id: str
    user_id: str
    ticker: str
    condition: str
    target_price: str
    current_price: str
    occurred_at: str