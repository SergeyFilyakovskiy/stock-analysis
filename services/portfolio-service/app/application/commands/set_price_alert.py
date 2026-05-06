from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities import PriceAlert
from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.domain.value_objects import Money, Ticker
from app.infrastructure.db.unit_of_work import UnitOfWork


@dataclass
class SetPriceAlertCommand:
    portfolio_id: UUID
    user_id: UUID
    ticker: str
    condition: str                 # "ABOVE" | "BELOW"
    target_price: Decimal
    currency: str = "USD"


class SetPriceAlertHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: SetPriceAlertCommand) -> UUID:
        portfolio = await self._uow.portfolios.get_by_id(command.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(command.portfolio_id))
        if portfolio.user_id != command.user_id:
            raise PortfolioAccessDenied(str(command.portfolio_id))

        alert = PriceAlert(
            id=uuid4(),
            portfolio_id=command.portfolio_id,
            user_id=command.user_id,
            ticker=Ticker(command.ticker),
            condition=command.condition.upper(),
            target_price=Money(command.target_price, command.currency),
        )
        await self._uow.alerts.save(alert)
        await self._uow.commit_with_events([])
        return alert.id