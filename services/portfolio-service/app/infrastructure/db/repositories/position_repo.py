from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Position
from app.domain.interfaces.i_position_repo import IPositionRepo
from app.domain.value_objects import Money, Quantity, Ticker
from app.infrastructure.db.models import PositionModel


class PositionRepo(IPositionRepo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_portfolio(self, portfolio_id: UUID) -> list[Position]:
        result = await self._session.execute(
            select(PositionModel).where(PositionModel.portfolio_id == portfolio_id)
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    async def save(self, position: Position) -> None:
        result = await self._session.execute(
            select(PositionModel).where(
                PositionModel.portfolio_id == position.portfolio_id,
                PositionModel.ticker == str(position.ticker),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.quantity = position.quantity.value
            existing.avg_price = position.avg_price.amount
        else:
            from uuid import uuid4
            self._session.add(
                PositionModel(
                    id=uuid4(),
                    portfolio_id=position.portfolio_id,
                    ticker=str(position.ticker),
                    quantity=position.quantity.value,
                    avg_price=position.avg_price.amount,
                    currency=position.avg_price.currency,
                )
            )

    async def delete_by_portfolio(self, portfolio_id: UUID) -> None:
        await self._session.execute(
            delete(PositionModel).where(PositionModel.portfolio_id == portfolio_id)
        )

    @staticmethod
    def _to_entity(row: PositionModel) -> Position:
        return Position(
            portfolio_id=row.portfolio_id,
            ticker=Ticker(row.ticker),
            quantity=Quantity(row.quantity),
            avg_price=Money(row.avg_price, row.currency),
        )