from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.entities import Portfolio
from app.domain.events import PortfolioCreated
from app.infrastructure.db.unit_of_work import UnitOfWork


@dataclass
class CreatePortfolioCommand:
    user_id: UUID
    name: str
    currency: str = "USD"


class CreatePortfolioHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: CreatePortfolioCommand) -> UUID:
        portfolio = Portfolio(
            id=uuid4(),
            user_id=command.user_id,
            name=command.name,
            currency=command.currency.upper(),
            created_at=datetime.now(timezone.utc),
        )
        domain_event = PortfolioCreated(
            portfolio_id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
        )
        await self._uow.portfolios.save(portfolio)
        await self._uow.commit_with_events([domain_event])
        return portfolio.id