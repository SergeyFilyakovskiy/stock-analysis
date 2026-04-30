from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import User
from app.domain.exceptions import UserNotFoundError
from app.domain.interfaces.i_user_repo import IUserRepo


@dataclass
class GetUserProfileQuery:
    user_id: UUID


@dataclass
class UserProfileDTO:
    id:           UUID
    email:        str
    role:         str
    first_name:   str | None
    last_name:    str | None
    bio:          str | None
    avatar_url:   str | None
    is_verified:  bool
    full_name:    str | None


class GetUserProfileHandler:

    def __init__(self, user_repo: IUserRepo) -> None:
        self.user_repo = user_repo

    async def handle(self, query: GetUserProfileQuery) -> UserProfileDTO:

        user = await self.user_repo.get_by_id(query.user_id)

        if not user:
            raise UserNotFoundError(f"User {query.user_id} not found")

        return self._to_dto(user)

    def _to_dto(self, user: User) -> UserProfileDTO:
        return UserProfileDTO(
            id=user.id,
            email=user.email.value,
            role=user.role.value,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            bio=user.profile.bio,
            avatar_url=user.profile.avatar_url,
            is_verified=user.is_verified,
            full_name=user.profile.full_name,
        )