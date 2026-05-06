from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.events import DomainEvent, TransactionAdded
from app.domain.exceptions import InsufficientPosition
from app.domain.value_objects import Money, Quantity, Ticker


@dataclass
class Position:
    portfolio_id: UUID
    ticker: Ticker
    quantity: Quantity
    avg_price: Money

    @property
    def market_value(self, current_price: Decimal | None = None) -> Decimal:
        if current_price is None:
            return self.avg_price.amount * self.quantity.value
        return current_price * self.quantity.value

    def unrealized_pnl(self, current_price: Decimal) -> Decimal:
        return (current_price - self.avg_price.amount) * self.quantity.value


@dataclass
class Transaction:
    id: UUID
    portfolio_id: UUID
    ticker: Ticker
    transaction_type: str          # "BUY" | "SELL"
    price: Money
    quantity: Quantity
    created_at: datetime


@dataclass
class PriceAlert:
    id: UUID
    portfolio_id: UUID
    user_id: UUID
    ticker: Ticker
    condition: str                 # "ABOVE" | "BELOW"
    target_price: Money
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WatchlistItem:
    id: UUID
    watchlist_id: UUID
    ticker: Ticker
    added_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Watchlist:
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    items: list[WatchlistItem] = field(default_factory=list)


@dataclass
class Portfolio:
    id: UUID
    user_id: UUID
    name: str
    currency: str
    version: int = 0               # optimistic locking
    created_at: datetime = field(default_factory=datetime.utcnow)
    positions: list[Position] = field(default_factory=list)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    # ── Domain logic ──────────────────────────────────────────────────────────

    def apply_buy(
        self,
        ticker: Ticker,
        quantity: Quantity,
        price: Money,
        transaction_id: UUID,
    ) -> Transaction:
        existing = self._find_position(ticker)
        if existing:
            total_qty = existing.quantity.value + quantity.value
            new_avg = (
                (existing.avg_price.amount * existing.quantity.value + price.amount * quantity.value)
                / total_qty
            )
            existing.quantity = Quantity(total_qty)
            existing.avg_price = Money(new_avg, price.currency)
        else:
            self.positions.append(
                Position(
                    portfolio_id=self.id,
                    ticker=ticker,
                    quantity=quantity,
                    avg_price=price,
                )
            )

        tx = Transaction(
            id=transaction_id,
            portfolio_id=self.id,
            ticker=ticker,
            transaction_type="BUY",
            price=price,
            quantity=quantity,
            created_at=datetime.utcnow(),
        )
        self._events.append(
            TransactionAdded(
                portfolio_id=self.id,
                ticker=str(ticker),
                transaction_type="BUY",
                quantity=quantity.value,
                price=price.amount,
            )
        )
        return tx

    def apply_sell(
        self,
        ticker: Ticker,
        quantity: Quantity,
        price: Money,
        transaction_id: UUID,
    ) -> Transaction:
        existing = self._find_position(ticker)
        if not existing:
            raise InsufficientPosition(str(ticker), "0", str(quantity.value))

        try:
            new_qty = existing.quantity - quantity
        except ValueError:
            raise InsufficientPosition(
                str(ticker),
                str(existing.quantity.value),
                str(quantity.value),
            )

        existing.quantity = new_qty
        if new_qty.is_zero():
            existing.avg_price = Money(Decimal("0"), existing.avg_price.currency)

        tx = Transaction(
            id=transaction_id,
            portfolio_id=self.id,
            ticker=ticker,
            transaction_type="SELL",
            price=price,
            quantity=quantity,
            created_at=datetime.utcnow(),
        )
        self._events.append(
            TransactionAdded(
                portfolio_id=self.id,
                ticker=str(ticker),
                transaction_type="SELL",
                quantity=quantity.value,
                price=price.amount,
            )
        )
        return tx

    def collect_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

    def _find_position(self, ticker: Ticker) -> Position | None:
        return next((p for p in self.positions if p.ticker == ticker), None)