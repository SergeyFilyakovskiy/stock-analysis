from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import PortfolioDTO, PositionDTO
from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.infrastructure.db.models import PortfolioModel, PositionModel


@dataclass
class GetPortfolioQuery:
    portfolio_id: UUID
    user_id: UUID


class GetPortfolioHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, query: GetPortfolioQuery) -> PortfolioDTO:
        portfolio = await self._session.get(PortfolioModel, query.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(query.portfolio_id))
        if portfolio.user_id != query.user_id:
            raise PortfolioAccessDenied(str(query.portfolio_id))

        result = await self._session.execute(
            select(PositionModel).where(PositionModel.portfolio_id == query.portfolio_id)
        )
        positions = result.scalars().all()

        return PortfolioDTO(
            id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
            currency=portfolio.currency,
            created_at=portfolio.created_at,
            positions=[
                PositionDTO(
                    ticker=p.ticker,
                    quantity=p.quantity,
                    avg_price=p.avg_price,
                    currency=p.currency,
                )
                for p in positions
            ],
        )