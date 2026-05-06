from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import WatchlistNotFound, WatchlistAccessDenied
from app.infrastructure.db.models import WatchlistModel, WatchlistItemModel


@dataclass
class RemoveFromWatchlistCommand:
    watchlist_id: UUID
    user_id: UUID
    ticker: str


class RemoveFromWatchlistHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, command: RemoveFromWatchlistCommand) -> None:
        wl = await self._session.get(WatchlistModel, command.watchlist_id)
        if not wl:
            raise WatchlistNotFound(str(command.watchlist_id))
        if wl.user_id != command.user_id:
            raise WatchlistAccessDenied(str(command.watchlist_id))

        await self._session.execute(
            delete(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == command.watchlist_id,
                WatchlistItemModel.ticker == command.ticker.upper(),
            )
        )
        await self._session.commit()