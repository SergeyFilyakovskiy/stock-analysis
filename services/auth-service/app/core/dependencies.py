# app/core/dependencies.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.commands.login_user import LoginUserHandler
from app.application.commands.logout_user import LogoutUserHandler
from app.application.commands.oauth_login import OAuthLoginHandler
from app.application.commands.refresh_token import RefreshTokenHandler
from app.application.commands.register_user import RegisterUserHandler
from app.application.queries.get_user_profile import GetUserProfileHandler
from app.application.queries.verify_token import VerifyTokenHandler
from app.application.services.token_service import TokenService
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.cache.token_store import RedisTokenStore
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.session import async_session
from app.infrastructure.external.github_oauth import GitHubOAuthProvider
from app.infrastructure.external.google_oauth import GoogleOAuthProvider

bearer_scheme = HTTPBearer(auto_error=False)


# ── Инфраструктурные зависимости ──────────────────────────

async def get_user_repo():
    async with async_session() as session:
        try:
            yield UserRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_token_store() -> RedisTokenStore:
    redis = await get_redis()
    return RedisTokenStore(redis)


def get_token_service() -> TokenService:
    return TokenService()


# ── OAuth провайдеры ──────────────────────────────────────

def get_google_provider() -> GoogleOAuthProvider:
    return GoogleOAuthProvider()


def get_github_provider() -> GitHubOAuthProvider:
    return GitHubOAuthProvider()


# ── Хэндлеры команд ──────────────────────────────────────

def get_register_handler(
    user_repo = Depends(get_user_repo),
) -> RegisterUserHandler:
    return RegisterUserHandler(user_repo)


def get_login_handler(
    user_repo     = Depends(get_user_repo),
    token_store   = Depends(get_token_store),
    token_service = Depends(get_token_service),
) -> LoginUserHandler:
    return LoginUserHandler(user_repo, token_store, token_service)


def get_refresh_handler(
    user_repo     = Depends(get_user_repo),
    token_store   = Depends(get_token_store),
    token_service = Depends(get_token_service),
) -> RefreshTokenHandler:
    return RefreshTokenHandler(user_repo, token_store, token_service)


def get_logout_handler(
    token_store   = Depends(get_token_store),
    token_service = Depends(get_token_service),
) -> LogoutUserHandler:
    return LogoutUserHandler(token_store, token_service)


def get_oauth_login_handler(
    user_repo     = Depends(get_user_repo),
    token_store   = Depends(get_token_store),
    token_service = Depends(get_token_service),
) -> OAuthLoginHandler:
    return OAuthLoginHandler(user_repo, token_store, token_service)


# ── Хэндлеры запросов ────────────────────────────────────

def get_verify_handler(
    token_store   = Depends(get_token_store),
    token_service = Depends(get_token_service),
) -> VerifyTokenHandler:
    return VerifyTokenHandler(token_store, token_service)


def get_profile_handler(
    user_repo = Depends(get_user_repo),
) -> GetUserProfileHandler:
    return GetUserProfileHandler(user_repo)


# ── Извлечение токена из заголовка ────────────────────────

async def get_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    return credentials.credentials