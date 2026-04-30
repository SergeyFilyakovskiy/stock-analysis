# app/domain/interfaces/i_user_repo.py
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities import User, OAuthAccount


class IUserRepo(ABC):

    # ── User CRUD ─────────────────────────────────────────

    @abstractmethod
    async def save(self, user: User) -> None:
        """Создать или обновить пользователя"""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Soft delete — выставляет is_active=False"""
        ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Проверка без загрузки всего объекта — быстрее чем get_by_email"""
        ...

    # ── OAuthAccount ──────────────────────────────────────

    @abstractmethod
    async def save_oauth_account(self, account: OAuthAccount) -> None:
        ...

    @abstractmethod
    async def get_oauth_account(
        self,
        provider: str,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        ...

    @abstractmethod
    async def get_oauth_accounts_by_user(
        self,
        user_id: UUID,
    ) -> list[OAuthAccount]:
        """Все привязанные OAuth-аккаунты пользователя"""
        ...

    @abstractmethod
    async def delete_oauth_account(
        self,
        provider: str,
        user_id: UUID,
    ) -> None:
        """Отвязать провайдера от аккаунта"""
        ...