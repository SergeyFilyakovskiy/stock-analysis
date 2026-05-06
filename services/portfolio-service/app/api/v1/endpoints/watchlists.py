from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.watchlists import (
    WatchlistCreateRequest,
    WatchlistItemAddRequest,
    WatchlistListResponse,
    WatchlistResponse,
    WatchlistItemResponse,
)
from app.application.commands.add_to_watchlist import AddToWatchlistCommand, AddToWatchlistHandler
from app.application.commands.remove_from_watchlist import (
    RemoveFromWatchlistCommand,
    RemoveFromWatchlistHandler,
)
from app.application.queries.get_watchlist import (
    GetAllWatchlistsHandler,
    GetAllWatchlistsQuery,
    GetWatchlistHandler,
    GetWatchlistQuery,
)
from app.core.dependencies import get_current_user_id, get_session
from app.domain.exceptions import (
    DuplicateWatchlistItem,
    WatchlistAccessDenied,
    WatchlistNotFound,
)
from app.infrastructure.db.models import WatchlistModel

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=list[WatchlistListResponse])
async def list_watchlists(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    handler = GetAllWatchlistsHandler(session)
    watchlists = await handler.handle(GetAllWatchlistsQuery(user_id=user_id))
    return [
        WatchlistListResponse(id=wl.id, name=wl.name, created_at=wl.created_at)
        for wl in watchlists
    ]


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    body: WatchlistCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    wl = WatchlistModel(
        id=uuid4(),
        user_id=user_id,
        name=body.name,
        created_at=datetime.now(timezone.utc),
    )
    session.add(wl)
    await session.commit()
    return WatchlistResponse(
        id=wl.id, name=wl.name, user_id=wl.user_id, created_at=wl.created_at, items=[]
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        handler = GetWatchlistHandler(session)
        wl = await handler.handle(GetWatchlistQuery(watchlist_id=watchlist_id, user_id=user_id))
    except WatchlistNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WatchlistAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return WatchlistResponse(
        id=wl.id,
        name=wl.name,
        user_id=wl.user_id,
        created_at=wl.created_at,
        items=[
            WatchlistItemResponse(id=i.id, ticker=i.ticker, added_at=i.added_at)
            for i in wl.items
        ],
    )


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    wl = await session.get(WatchlistModel, watchlist_id)
    if not wl:
        raise HTTPException(status_code=404, detail=f"Watchlist {watchlist_id} not found")
    if wl.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await session.delete(wl)
    await session.commit()


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    watchlist_id: UUID,
    body: WatchlistItemAddRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        handler = AddToWatchlistHandler(session)
        item_id = await handler.handle(
            AddToWatchlistCommand(
                watchlist_id=watchlist_id,
                user_id=user_id,
                ticker=body.ticker,
            )
        )
    except WatchlistNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WatchlistAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))
    except DuplicateWatchlistItem as e:
        raise HTTPException(status_code=409, detail=str(e))

    return WatchlistItemResponse(
        id=item_id,
        ticker=body.ticker.upper(),
        added_at=datetime.now(timezone.utc),
    )


@router.delete("/{watchlist_id}/items/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    watchlist_id: UUID,
    ticker: str,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        handler = RemoveFromWatchlistHandler(session)
        await handler.handle(
            RemoveFromWatchlistCommand(
                watchlist_id=watchlist_id,
                user_id=user_id,
                ticker=ticker,
            )
        )
    except WatchlistNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WatchlistAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))