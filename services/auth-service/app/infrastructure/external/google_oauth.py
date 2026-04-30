# app/infrastructure/external/google_oauth.py
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from app.domain.interfaces.i_oauth_provider import IOAuthProvider, OAuthUserInfo
from app.infrastructure.external.oauth_registry import oauth


class GoogleOAuthProvider(IOAuthProvider):

    @property
    def provider_name(self) -> str:
        return "google"

    async def get_redirect_url(
        self,
        request: Request,
        redirect_uri: str,
    ) -> Response:
        return await oauth.google.authorize_redirect(request, redirect_uri)

    async def get_user_info(self, request: Request) -> OAuthUserInfo:
        # Меняем code на токен + автоматически получаем userinfo через OIDC
        token = await oauth.google.authorize_access_token(request)

        # Google возвращает userinfo прямо в токене (OIDC id_token)
        userinfo = token.get("userinfo")
        if not userinfo:
            # Fallback — запрашиваем userinfo напрямую
            resp = await oauth.google.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                token=token,
            )
            userinfo = resp.json()

        return OAuthUserInfo(
            provider=self.provider_name,
            provider_user_id=userinfo["sub"],        # уникальный ID в Google
            email=userinfo["email"],
            name=userinfo.get("name"),
            avatar_url=userinfo.get("picture"),
            provider_email=userinfo["email"],
        )