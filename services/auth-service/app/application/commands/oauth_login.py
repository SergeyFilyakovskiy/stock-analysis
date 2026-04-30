# app/application/commands/oauth_login.py
from __future__ import annotations

import uuid

from app.application.dto import TokenPairDTO
from app.application.services.token_service import TokenService
from app.domain.entities import OAuthAccount, User, UserProfile
from app.domain.interfaces.i_oauth_provider import OAuthUserInfo
from app.domain.interfaces.i_token_store import ITokenStore
from app.domain.interfaces.i_user_repo import IUserRepo
from app.domain.value_objects import Email, Role


class OAuthLoginHandler:

    def __init__(
        self,
        user_repo:     IUserRepo,
        token_store:   ITokenStore,
        token_service: TokenService,
    ) -> None:
        self.user_repo     = user_repo
        self.token_store   = token_store
        self.token_service = token_service

    async def handle(self, user_info: OAuthUserInfo) -> TokenPairDTO:

        # 1. Ищем уже привязанный OAuth-аккаунт
        oauth_account = await self.user_repo.get_oauth_account(
            provider=user_info.provider,
            provider_user_id=user_info.provider_user_id,
        )

        if oauth_account:
            # Уже заходил через этот провайдер — просто логиним
            user = await self.user_repo.get_by_id(oauth_account.user_id)
        else:
            # Ищем юзера по email — мог регистрироваться обычным способом
            user = await self.user_repo.get_by_email(user_info.email)

            if not user:
                # Первый вход — создаём нового пользователя
                user = User(
                    id=uuid.uuid4(),
                    email=Email(user_info.email),
                    hashed_password=None,   # OAuth-юзер без пароля
                    role=Role(Role.USER),
                    is_active=True,
                    is_verified=True,       # email уже подтверждён провайдером
                    profile=UserProfile(
                        first_name=user_info.name.split()[0]
                                   if user_info.name else None,
                        last_name=" ".join(user_info.name.split()[1:]) or None
                                  if user_info.name else None,
                        avatar_url=user_info.avatar_url,
                    ),
                )
                await self.user_repo.save(user)

            # Привязываем OAuth-аккаунт к пользователю
            oauth_account = OAuthAccount(
                id=uuid.uuid4(),
                user_id=user.id,
                provider=user_info.provider,
                provider_user_id=user_info.provider_user_id,
                provider_email=user_info.provider_email or user_info.email,
            )
            await self.user_repo.save_oauth_account(oauth_account)

        return await self.token_service.create_token_pair(user, self.token_store) # type: ignore