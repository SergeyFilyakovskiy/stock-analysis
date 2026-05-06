from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import WatchlistNotFound, WatchlistAccessDenied, DuplicateWatchlistItem
from app.domain.value_objects import Ticker
from app.infrastructure.db.models import WatchlistModel, WatchlistItemModel


@dataclass
class AddToWatchlistCommand:
    watchlist_id: UUID
    user_id: UUID
    ticker: str


class AddToWatchlistHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, command: AddToWatchlistCommand) -> UUID:
        ticker = Ticker(command.ticker)

        wl = await self._session.get(WatchlistModel, command.watchlist_id)
        if not wl:
            raise WatchlistNotFound(str(command.watchlist_id))
        if wl.user_id != command.user_id:
            raise WatchlistAccessDenied(str(command.watchlist_id))

        # Проверка дубликата
        result = await self._session.execute(
            select(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == command.watchlist_id,
                WatchlistItemModel.ticker == str(ticker),
            )
        )
        if result.scalar_one_or_none():
            raise DuplicateWatchlistItem(str(ticker), str(command.watchlist_id))

        item = WatchlistItemModel(
            id=uuid4(),
            watchlist_id=command.watchlist_id,
            ticker=str(ticker),
            added_at=datetime.now(timezone.utc),
        )
        self._session.add(item)
        await self._session.commit()
        return item.id