# app/domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from app.domain.value_objects import Email, Role, HashedPassword, UserProfile


@dataclass
class User:

    id:                 UUID
    email:              Email
    role:               Role
    profile:            UserProfile
    hashed_password:    HashedPassword | None = None
    is_active:          bool = True
    is_verified:        bool = False
    created_at:         datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:         datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def change_email(self, new_email: str) -> None:
        object.__setattr__(self, 'email', Email(new_email))

    def verify_password(self, plain: str) -> bool:
        if self.hashed_password is None:
            return False
        return self.hashed_password.verify(plain)

    def is_admin(self) -> bool:
        return self.role.is_admin()
    
    def is_oauth_only(self) -> bool:
        """Пользователь без пароля — только OAuth"""
        return self.hashed_password is None

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def verify_email(self) -> None:
        self.is_verified = True
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(self, **kwargs) -> None:
        self.profile.update(**kwargs)
        self.updated_at = datetime.now(timezone.utc)

    
# ── OAuthAccount — привязанный OAuth-аккаунт ─────────────

@dataclass
class OAuthAccount:
    """
    Один User может иметь несколько OAuthAccount
    (Google + GitHub привязаны к одному аккаунту)
    """
    id:               UUID
    user_id:          UUID
    provider:         str        
    provider_user_id: str
    provider_email:   str
    access_token:     str | None = None
    refresh_token:    str | None = None
    expires_at:       datetime | None = None
    created_at:       datetime = field(default_factory=datetime.now(timezone.utc)) #type: ignore

    def is_token_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at