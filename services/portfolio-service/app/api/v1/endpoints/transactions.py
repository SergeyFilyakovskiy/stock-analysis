from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.transactions import (
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
)
from app.application.commands.add_transaction import AddTransactionCommand, AddTransactionHandler
from app.application.queries.get_transactions import GetTransactionsHandler, GetTransactionsQuery
from app.core.dependencies import get_current_user_id, get_pnl_cache, get_session, get_uow
from app.domain.exceptions import (
    InsufficientPosition,
    PortfolioAccessDenied,
    PortfolioNotFound,
)
from app.infrastructure.cache.pnl_cache import PnlCache
from app.infrastructure.db.repositories.portfolio_repo import PortfolioRepo
from app.infrastructure.db.repositories.transaction_repo import TransactionRepo
from app.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/portfolios", tags=["transactions"])


@router.post(
    "/{portfolio_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_transaction(
    portfolio_id: UUID,
    body: TransactionCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
    pnl_cache: PnlCache = Depends(get_pnl_cache),
):
    try:
        handler = AddTransactionHandler(uow, pnl_cache)
        tx_id = await handler.handle(
            AddTransactionCommand(
                portfolio_id=portfolio_id,
                user_id=user_id,
                ticker=body.ticker,
                transaction_type=body.transaction_type,
                price=body.price,
                quantity=body.quantity,
                currency=body.currency,
            )
        )
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InsufficientPosition as e:
        raise HTTPException(status_code=422, detail=str(e))

    return TransactionResponse(
        id=tx_id,
        ticker=body.ticker.upper(),
        transaction_type=body.transaction_type,
        price=body.price,
        quantity=body.quantity,
        currency=body.currency,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/{portfolio_id}/transactions", response_model=TransactionListResponse)
async def get_transactions(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session=Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        handler = GetTransactionsHandler(
            PortfolioRepo(session), TransactionRepo(session)
        )
        items = await handler.handle(
            GetTransactionsQuery(
                portfolio_id=portfolio_id,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        )
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return TransactionListResponse(
        items=[
            TransactionResponse(
                id=tx.id,
                ticker=tx.ticker,
                transaction_type=tx.transaction_type,
                price=tx.price,
                quantity=tx.quantity,
                currency=tx.currency,
                created_at=tx.created_at,
            )
            for tx in items
        ],
        total=len(items),
        limit=limit,
        offset=offset,
    )