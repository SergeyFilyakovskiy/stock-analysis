from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.cache.pnl_cache import PnlCache


@dataclass
class DeletePortfolioCommand:
    portfolio_id: UUID
    user_id: UUID


class DeletePortfolioHandler:
    def __init__(self, uow: UnitOfWork, pnl_cache: PnlCache) -> None:
        self._uow = uow
        self._pnl_cache = pnl_cache

    async def handle(self, command: DeletePortfolioCommand) -> None:
        portfolio = await self._uow.portfolios.get_by_id(command.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(command.portfolio_id))
        if portfolio.user_id != command.user_id:
            raise PortfolioAccessDenied(str(command.portfolio_id))

        await self._uow.portfolios.delete(command.portfolio_id)
        await self._uow.commit_with_events([])
        await self._pnl_cache.invalidate(command.portfolio_id)