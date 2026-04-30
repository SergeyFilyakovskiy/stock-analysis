from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.entities import User, OAuthAccount, UserProfile
from app.domain.interfaces.i_user_repo import IUserRepo
from app.domain.value_objects import Email, HashedPassword, Role
from app.infrastructure.db.models import OAuthAccountORM, ProfileORM, UserORM


class UserRepository(IUserRepo):

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── User CRUD ─────────────────────────────────────────

    async def save(self, user: User) -> None:
        orm = await self.session.get(UserORM, user.id)

        if orm is None:
            # Создаём нового пользователя
            orm = self._user_to_orm(user)
            self.session.add(orm)

            # Профиль создаётся вместе с юзером
            profile_orm = self._profile_to_orm(user.id, user.profile)
            self.session.add(profile_orm)
        else:
            # Обновляем существующего
            orm.email       = user.email.value
            orm.role        = user.role.as_enum
            orm.is_active   = user.is_active
            orm.is_verified = user.is_verified
            orm.hashed_password = (
                user.hashed_password.value
                if user.hashed_password else None
            )

    async def get_by_id(self, user_id: UUID) -> User | None:
        orm = await self.session.scalar(
            select(UserORM)
            .options(joinedload(UserORM.profile))
            .where(UserORM.id == user_id)
        )
        return self._to_entity(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        orm = await self.session.scalar(
            select(UserORM)
            .options(joinedload(UserORM.profile))
            .where(UserORM.email == email.lower())
        )
        return self._to_entity(orm) if orm else None

    async def delete(self, user_id: UUID) -> None:
        """Soft delete — не удаляем физически, просто деактивируем"""
        orm = await self.session.get(UserORM, user_id)
        if orm:
            orm.is_active = False

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.scalar(
            select(exists().where(UserORM.email == email.lower()))
        )
        return bool(result)

    # ── Profile ───────────────────────────────────────────

    async def get_profile(self, user_id: UUID) -> UserProfile | None:
        orm = await self.session.scalar(
            select(ProfileORM).where(ProfileORM.user_id == user_id)
        )
        return self._profile_to_entity(orm) if orm else None

    async def update_profile(self, user_id: UUID, profile: UserProfile) -> None:
        orm = await self.session.scalar(
            select(ProfileORM).where(ProfileORM.user_id == user_id)
        )
        if orm is None:
            # Профиль мог не создаться — создаём
            orm = self._profile_to_orm(user_id, profile)
            self.session.add(orm)
        else:
            orm.first_name = profile.first_name
            orm.last_name  = profile.last_name
            orm.bio        = profile.bio
            orm.avatar_url = profile.avatar_url

    # ── OAuthAccount ──────────────────────────────────────

    async def save_oauth_account(self, account: OAuthAccount) -> None:
        existing = await self.session.scalar(
            select(OAuthAccountORM).where(
                OAuthAccountORM.provider         == account.provider,
                OAuthAccountORM.provider_user_id == account.provider_user_id,
            )
        )
        if existing is None:
            self.session.add(self._oauth_to_orm(account))
        else:
            # Обновляем токены провайдера если изменились
            existing.access_token  = account.access_token
            existing.refresh_token = account.refresh_token
            existing.expires_at    = account.expires_at

    async def get_oauth_account(
        self,
        provider: str,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        orm = await self.session.scalar(
            select(OAuthAccountORM).where(
                OAuthAccountORM.provider         == provider,
                OAuthAccountORM.provider_user_id == provider_user_id,
            )
        )
        return self._oauth_to_entity(orm) if orm else None

    async def get_oauth_accounts_by_user(
        self,
        user_id: UUID,
    ) -> list[OAuthAccount]:
        result = await self.session.scalars(
            select(OAuthAccountORM).where(OAuthAccountORM.user_id == user_id)
        )
        return [self._oauth_to_entity(orm) for orm in result.all()]

    async def delete_oauth_account(self, provider: str, user_id: UUID) -> None:
        orm = await self.session.scalar(
            select(OAuthAccountORM).where(
                OAuthAccountORM.provider == provider,
                OAuthAccountORM.user_id  == user_id,
            )
        )
        if orm:
            await self.session.delete(orm)

    # ── Маппинг ORM → Entity ──────────────────────────────

    def _to_entity(self, orm: UserORM) -> User:
        return User(
            id=orm.id,
            email=Email(orm.email),
            role=Role(orm.role.value),
            hashed_password=(
                HashedPassword.from_hash(orm.hashed_password)
                if orm.hashed_password else None
            ),
            is_active=orm.is_active,
            is_verified=orm.is_verified,
            profile=self._profile_to_entity(orm.profile) if orm.profile
                    else UserProfile(),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _profile_to_entity(self, orm: ProfileORM) -> UserProfile:
        return UserProfile(
            first_name=orm.first_name,
            last_name=orm.last_name,
            bio=orm.bio,
            avatar_url=orm.avatar_url,
        )

    def _oauth_to_entity(self, orm: OAuthAccountORM) -> OAuthAccount:
        return OAuthAccount(
            id=orm.id,
            user_id=orm.user_id,
            provider=orm.provider,
            provider_user_id=orm.provider_user_id,
            provider_email=orm.provider_email,
            access_token=orm.access_token,
            refresh_token=orm.refresh_token,
            expires_at=orm.expires_at,
        )

    # ── Маппинг Entity → ORM ──────────────────────────────

    def _user_to_orm(self, user: User) -> UserORM:
        return UserORM(
            id=user.id,
            email=user.email.value,
            role=user.role.as_enum,
            hashed_password=(
                user.hashed_password.value
                if user.hashed_password else None
            ),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _profile_to_orm(self, user_id: UUID, profile: UserProfile) -> ProfileORM:
        return ProfileORM(
            id=uuid.uuid4(),
            user_id=user_id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
        )

    def _oauth_to_orm(self, account: OAuthAccount) -> OAuthAccountORM:
        return OAuthAccountORM(
            id=account.id,
            user_id=account.user_id,
            provider=account.provider,
            provider_user_id=account.provider_user_id,
            provider_email=account.provider_email,
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            expires_at=account.expires_at,
        )