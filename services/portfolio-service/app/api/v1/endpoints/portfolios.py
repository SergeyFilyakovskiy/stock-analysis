from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.portfolios import (
    PortfolioCreateRequest,
    PortfolioListResponse,
    PortfolioResponse,
)
from app.application.commands.create_portfolio import CreatePortfolioCommand, CreatePortfolioHandler
from app.application.commands.delete_portfolio import DeletePortfolioCommand, DeletePortfolioHandler
from app.application.queries.get_portfolio import GetPortfolioHandler, GetPortfolioQuery
from app.core.dependencies import get_current_user_id, get_pnl_cache, get_uow, get_session
from app.domain.exceptions import PortfolioAccessDenied, PortfolioNotFound
from app.infrastructure.cache.pnl_cache import PnlCache
from app.infrastructure.db.models import PortfolioModel
from app.infrastructure.db.unit_of_work import UnitOfWork
from sqlalchemy import select

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=list[PortfolioListResponse])
async def list_portfolios(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PortfolioModel).where(PortfolioModel.user_id == user_id)
    )
    portfolios = result.scalars().all()
    return [
        PortfolioListResponse(
            id=p.id,
            name=p.name,
            currency=p.currency,
            created_at=p.created_at,
        )
        for p in portfolios
    ]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    body: PortfolioCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
    session: AsyncSession = Depends(get_session),
):
    handler = CreatePortfolioHandler(uow)
    portfolio_id = await handler.handle(
        CreatePortfolioCommand(user_id=user_id, name=body.name, currency=body.currency)
    )
    query_handler = GetPortfolioHandler(session)
    return await query_handler.handle(GetPortfolioQuery(portfolio_id=portfolio_id, user_id=user_id))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        handler = GetPortfolioHandler(session)
        return await handler.handle(GetPortfolioQuery(portfolio_id=portfolio_id, user_id=user_id))
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
    pnl_cache: PnlCache = Depends(get_pnl_cache),
):
    try:
        handler = DeletePortfolioHandler(uow, pnl_cache)
        await handler.handle(DeletePortfolioCommand(portfolio_id=portfolio_id, user_id=user_id))
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))