# app/domain/interfaces/i_oauth_provider.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from starlette.requests import Request
from starlette.responses import Response


@dataclass
class OAuthUserInfo:
    """Нормализованные данные пользователя от любого провайдера"""
    provider:         str
    provider_user_id: str
    email:            str
    name:             str | None = None
    avatar_url:       str | None = None
    provider_email:   str | None = None


class IOAuthProvider(ABC):

    @abstractmethod
    async def get_redirect_url(
        self,
        request: Request,
        redirect_uri: str,
    ) -> Response:
        """Редирект пользователя на страницу логина провайдера"""
        ...

    @abstractmethod
    async def get_user_info(self, request: Request) -> OAuthUserInfo:
        """
        Обменять code на токен провайдера и получить данные пользователя.
        Вызывается в callback эндпоинте.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Имя провайдера: 'google' | 'github'"""
        ...