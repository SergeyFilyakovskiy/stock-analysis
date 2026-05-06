from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import OutboxEventModel


class OutboxRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending(self, batch_size: int = 50) -> list[OutboxEventModel]:
        result = await self._session.execute(
            select(OutboxEventModel)
            .where(OutboxEventModel.sent_at.is_(None))
            .order_by(OutboxEventModel.created_at)
            .limit(batch_size)
        )
        return list(result.scalars().all())

    async def mark_sent(self, event_ids: list[UUID]) -> None:
        if not event_ids:
            return
        await self._session.execute(
            update(OutboxEventModel)
            .where(OutboxEventModel.id.in_(event_ids))
            .values(sent_at=datetime.utcnow())
        )
        await self._session.commit()