# app/domain/interfaces/i_token_store.py
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID


class ITokenStore(ABC):

    # ── Refresh tokens ────────────────────────────────────

    @abstractmethod
    async def save_refresh_token(
        self,
        user_id: UUID,
        token: str,
        ttl: int,  # секунды
    ) -> None:
        """Сохранить refresh token с TTL"""
        ...

    @abstractmethod
    async def get_refresh_token(self, user_id: UUID) -> str | None:
        """Получить текущий refresh token пользователя"""
        ...

    @abstractmethod
    async def delete_refresh_token(self, user_id: UUID) -> None:
        """Удалить refresh token (logout / rotation)"""
        ...

    @abstractmethod
    async def refresh_token_exists(self, user_id: UUID, token: str) -> bool:
        """Проверить что токен существует и совпадает (защита от replay)"""
        ...

    # ── Blacklist access tokens ───────────────────────────

    @abstractmethod
    async def blacklist_token(
        self,
        jti: str,
        ttl: int,
    ) -> None:
        """Добавить access token в чёрный список (logout / смена пароля)"""
        ...

    @abstractmethod
    async def is_blacklisted(self, jti: str) -> bool:
        """Проверить токен при каждом запросе через Traefik forwardAuth"""
        ...

    # ── Failed login attempts (brute-force protection) ────

    @abstractmethod
    async def increment_failed_attempts(
        self,
        email: str,
        ttl: int,
    ) -> int:
        """Увеличить счётчик неудачных попыток, вернуть текущее значение"""
        ...

    @abstractmethod
    async def get_failed_attempts(self, email: str) -> int:
        ...

    @abstractmethod
    async def reset_failed_attempts(self, email: str) -> None:
        """Сбросить счётчик после успешного логина"""
        ...