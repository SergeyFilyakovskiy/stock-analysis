from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.queries.verify_token import VerifyTokenHandler, VerifyTokenQuery
from app.core.dependencies import get_access_token, get_verify_handler
from app.domain.exceptions import InvalidTokenError

router = APIRouter(prefix="/verify", tags=["Verify"])


@router.get("")
async def verify_token(
    response:     Response,
    access_token: str               = Depends(get_access_token),
    handler:      VerifyTokenHandler = Depends(get_verify_handler),
):
    """Вызывается Traefik forwardAuth на каждый запрос"""
    try:
        user = await handler.handle(VerifyTokenQuery(access_token=access_token))

        # Traefik прокидывает эти заголовки в downstream-сервисы
        response.headers["X-User-Id"]    = str(user.user_id)
        response.headers["X-User-Email"] = user.email
        response.headers["X-User-Role"]  = user.role

        return {"status": "ok"}
    except InvalidTokenError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))