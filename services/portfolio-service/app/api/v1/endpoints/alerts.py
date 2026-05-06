from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.alerts import AlertCreateRequest, AlertResponse
from app.application.commands.delete_price_alert import (
    DeletePriceAlertCommand,
    DeletePriceAlertHandler,
)
from app.application.commands.set_price_alert import SetPriceAlertCommand, SetPriceAlertHandler
from app.core.dependencies import get_current_user_id, get_uow
from app.domain.exceptions import AlertNotFound, PortfolioAccessDenied, PortfolioNotFound
from app.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    alerts = await uow.alerts.get_by_user(user_id)
    return [
        AlertResponse(
            id=a.id,
            portfolio_id=a.portfolio_id,
            ticker=str(a.ticker),
            condition=a.condition,
            target_price=a.target_price.amount,
            currency=a.target_price.currency,
            is_active=a.is_active,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    try:
        handler = SetPriceAlertHandler(uow)
        alert_id = await handler.handle(
            SetPriceAlertCommand(
                portfolio_id=body.portfolio_id,
                user_id=user_id,
                ticker=body.ticker,
                condition=body.condition,
                target_price=body.target_price,
                currency=body.currency,
            )
        )
    except PortfolioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioAccessDenied as e:
        raise HTTPException(status_code=403, detail=str(e))

    return AlertResponse(
        id=alert_id,
        portfolio_id=body.portfolio_id,
        ticker=body.ticker.upper(),
        condition=body.condition,
        target_price=body.target_price,
        currency=body.currency,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    try:
        handler = DeletePriceAlertHandler(uow)
        await handler.handle(DeletePriceAlertCommand(alert_id=alert_id, user_id=user_id))
    except AlertNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))