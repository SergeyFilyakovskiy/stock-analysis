from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Portfolio, Position
from app.domain.interfaces.i_portfolio_repo import IPortfolioRepo
from app.domain.value_objects import Money, Quantity, Ticker
from app.infrastructure.db.models import PortfolioModel, PositionModel


class PortfolioRepo(IPortfolioRepo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, portfolio_id: UUID) -> Portfolio | None:
        result = await self._session.execute(
            select(PortfolioModel).where(PortfolioModel.id == portfolio_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_all_by_user(self, user_id: UUID) -> list[Portfolio]:
        result = await self._session.execute(
            select(PortfolioModel).where(PortfolioModel.user_id == user_id)
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    async def save(self, portfolio: Portfolio) -> None:
        existing = await self._session.get(PortfolioModel, portfolio.id)
        if existing:
            existing.name = portfolio.name
            existing.currency = portfolio.currency
            existing.version = portfolio.version + 1
        else:
            self._session.add(
                PortfolioModel(
                    id=portfolio.id,
                    user_id=portfolio.user_id,
                    name=portfolio.name,
                    currency=portfolio.currency,
                    version=portfolio.version,
                    created_at=portfolio.created_at,
                )
            )

    async def delete(self, portfolio_id: UUID) -> None:
        await self._session.execute(
            delete(PortfolioModel).where(PortfolioModel.id == portfolio_id)
        )

    @staticmethod
    def _to_entity(row: PortfolioModel) -> Portfolio:
        return Portfolio(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            currency=row.currency,
            version=row.version,
            created_at=row.created_at,
        )