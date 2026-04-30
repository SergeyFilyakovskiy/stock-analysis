from __future__ import annotations

from dataclasses import dataclass

from app.application.dto import TokenPairDTO
from app.application.services.token_service import TokenService
from app.domain.exceptions import InvalidTokenError
from app.domain.interfaces.i_token_store import ITokenStore
from app.domain.interfaces.i_user_repo import IUserRepo


@dataclass
class RefreshTokenCommand:
    refresh_token: str


class RefreshTokenHandler:

    def __init__(
        self,
        user_repo:     IUserRepo,
        token_store:   ITokenStore,
        token_service: TokenService,
    ) -> None:
        self.user_repo     = user_repo
        self.token_store   = token_store
        self.token_service = token_service

    async def handle(self, command: RefreshTokenCommand) -> TokenPairDTO:

        # 1. Декодируем refresh token — проверяем подпись и срок
        payload = self.token_service.decode_token(command.refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token")

        user_id = payload["sub"]

        # 2. Проверяем что токен совпадает с сохранённым в Redis
        #    Защита от повторного использования украденного токена
        is_valid = await self.token_store.refresh_token_exists(
            user_id,
            command.refresh_token,
        )
        if not is_valid:
            raise InvalidTokenError("Refresh token not found or already used")

        # 3. Получаем пользователя
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        # 4. Удаляем старый refresh token (rotation)
        await self.token_store.delete_refresh_token(user_id)

        # 5. Выдаём новую пару токенов
        return await self.token_service.create_token_pair(user, self.token_store)