from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import PriceAlert
from app.domain.interfaces.i_alert_repo import IAlertRepo
from app.domain.value_objects import Money, Ticker
from app.infrastructure.db.models import PriceAlertModel


class AlertRepo(IAlertRepo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, alert: PriceAlert) -> None:
        self._session.add(
            PriceAlertModel(
                id=alert.id,
                portfolio_id=alert.portfolio_id,
                user_id=alert.user_id,
                ticker=str(alert.ticker),
                condition=alert.condition,
                target_price=alert.target_price.amount,
                currency=alert.target_price.currency,
                is_active=alert.is_active,
                created_at=alert.created_at,
            )
        )

    async def get_by_user(self, user_id: UUID) -> list[PriceAlert]:
        result = await self._session.execute(
            select(PriceAlertModel).where(PriceAlertModel.user_id == user_id)
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    async def get_active_by_ticker(self, ticker: str) -> list[PriceAlert]:
        result = await self._session.execute(
            select(PriceAlertModel).where(
                PriceAlertModel.ticker == ticker.upper(),
                PriceAlertModel.is_active.is_(True),
            )
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    async def delete(self, alert_id: UUID) -> None:
        result = await self._session.get(PriceAlertModel, alert_id)
        if result:
            await self._session.delete(result)

    async def deactivate(self, alert_id: UUID) -> None:
        await self._session.execute(
            update(PriceAlertModel)
            .where(PriceAlertModel.id == alert_id)
            .values(is_active=False)
        )

    @staticmethod
    def _to_entity(row: PriceAlertModel) -> PriceAlert:
        return PriceAlert(
            id=row.id,
            portfolio_id=row.portfolio_id,
            user_id=row.user_id,
            ticker=Ticker(row.ticker),
            condition=row.condition,
            target_price=Money(row.target_price, row.currency),
            is_active=row.is_active,
            created_at=row.created_at,
        )