from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.schemas.oauth import OAuthTokenResponse
from app.application.commands.oauth_login import OAuthLoginHandler
from app.core.dependencies import get_oauth_login_handler
from app.domain.interfaces.i_oauth_provider import IOAuthProvider
from app.infrastructure.external.github_oauth import GitHubOAuthProvider
from app.infrastructure.external.google_oauth import GoogleOAuthProvider

router = APIRouter(prefix="/oauth", tags=["OAuth"])


def _resolve_provider(provider: str) -> IOAuthProvider:
    providers = {
        "google": GoogleOAuthProvider,
        "github": GitHubOAuthProvider,
    }
    cls = providers.get(provider)
    if not cls:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Unknown provider: {provider}",
        )
    return cls()


@router.get("/{provider}")
async def oauth_redirect(provider: str, request: Request):
    """Редирект пользователя на страницу логина провайдера"""
    oauth_provider = _resolve_provider(provider)
    redirect_uri   = str(request.url_for("oauth_callback", provider=provider))
    return await oauth_provider.get_redirect_url(request, redirect_uri)


@router.get("/{provider}/callback", response_model=OAuthTokenResponse, name="oauth_callback")
async def oauth_callback(
    provider: str,
    request:  Request,
    handler:  OAuthLoginHandler = Depends(get_oauth_login_handler),
):
    """Callback — меняем code на токены"""
    try:
        oauth_provider = _resolve_provider(provider)
        user_info      = await oauth_provider.get_user_info(request)
        tokens         = await handler.handle(user_info)
        return OAuthTokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"OAuth error: {e}")