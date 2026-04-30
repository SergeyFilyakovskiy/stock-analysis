# app/infrastructure/external/github_oauth.py
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from app.domain.interfaces.i_oauth_provider import IOAuthProvider, OAuthUserInfo
from app.infrastructure.external.oauth_registry import oauth


class GitHubOAuthProvider(IOAuthProvider):

    @property
    def provider_name(self) -> str:
        return "github"

    async def get_redirect_url(
        self,
        request: Request,
        redirect_uri: str,
    ) -> Response:
        return await oauth.github.authorize_redirect(request, redirect_uri)

    async def get_user_info(self, request: Request) -> OAuthUserInfo:
        token = await oauth.github.authorize_access_token(request)

        # Основной профиль
        resp = await oauth.github.get("user", token=token)
        profile = resp.json()

        # GitHub не гарантирует email в профиле — нужен отдельный запрос
        primary_email = await self._get_primary_email(token)

        return OAuthUserInfo(
            provider=self.provider_name,
            provider_user_id=str(profile["id"]),     # уникальный ID в GitHub
            email=primary_email,
            name=profile.get("name") or profile.get("login"),
            avatar_url=profile.get("avatar_url"),
            provider_email=primary_email,
        )

    async def _get_primary_email(self, token: dict) -> str:
        """GitHub скрывает email — запрашиваем отдельно через user:email scope"""
        resp = await oauth.github.get("user/emails", token=token)
        emails = resp.json()

        # Ищем primary + verified email
        for email_obj in emails:
            if email_obj.get("primary") and email_obj.get("verified"):
                return email_obj["email"]

        # Fallback — первый verified
        for email_obj in emails:
            if email_obj.get("verified"):
                return email_obj["email"]

        raise ValueError("GitHub account has no verified email")