from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import WatchlistDTO, WatchlistItemDTO
from app.domain.exceptions import WatchlistNotFound, WatchlistAccessDenied
from app.infrastructure.db.models import WatchlistModel, WatchlistItemModel


@dataclass
class GetAllWatchlistsQuery:
    user_id: UUID


@dataclass
class GetWatchlistQuery:
    watchlist_id: UUID
    user_id: UUID


class GetAllWatchlistsHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, query: GetAllWatchlistsQuery) -> list[WatchlistDTO]:
        result = await self._session.execute(
            select(WatchlistModel).where(WatchlistModel.user_id == query.user_id)
        )
        watchlists = result.scalars().all()
        return [
            WatchlistDTO(
                id=wl.id, name=wl.name,
                user_id=wl.user_id, created_at=wl.created_at, items=[]
            )
            for wl in watchlists
        ]


class GetWatchlistHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def handle(self, query: GetWatchlistQuery) -> WatchlistDTO:
        wl = await self._session.get(WatchlistModel, query.watchlist_id)
        if not wl:
            raise WatchlistNotFound(str(query.watchlist_id))
        if wl.user_id != query.user_id:
            raise WatchlistAccessDenied(str(query.watchlist_id))

        result = await self._session.execute(
            select(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == query.watchlist_id
            )
        )
        items = result.scalars().all()

        return WatchlistDTO(
            id=wl.id,
            name=wl.name,
            user_id=wl.user_id,
            created_at=wl.created_at,
            items=[
                WatchlistItemDTO(id=i.id, ticker=i.ticker, added_at=i.added_at)
                for i in items
            ],
        )