from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import DomainEvent, TransactionAdded, AlertTriggered, PortfolioCreated
from app.infrastructure.db.models import OutboxEventModel
from app.infrastructure.db.repositories.portfolio_repo import PortfolioRepo
from app.infrastructure.db.repositories.position_repo import PositionRepo
from app.infrastructure.db.repositories.transaction_repo import TransactionRepo
from app.infrastructure.db.repositories.alert_repo import AlertRepo


_ROUTING_KEY_MAP: dict[type[DomainEvent], str] = {
    TransactionAdded: "portfolio.transaction.added",
    AlertTriggered:   "portfolio.alert.triggered",
    PortfolioCreated: "portfolio.created",
}


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.portfolios = PortfolioRepo(session)
        self.positions = PositionRepo(session)
        self.transactions = TransactionRepo(session)
        self.alerts = AlertRepo(session)

    async def commit_with_events(self, events: list[DomainEvent]) -> None:
        """Сохраняет Outbox-записи и делает единый commit."""
        for event in events:
            routing_key = _ROUTING_KEY_MAP.get(type(event), "portfolio.event")
            payload = json.dumps(event.__dict__, default=str)
            self._session.add(
                OutboxEventModel(
                    id=uuid4(),
                    event_type=type(event).__name__,
                    payload=payload,
                    routing_key=routing_key,
                )
            )
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()