from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings
from app.domain.exceptions import (
    InvalidCredentialsError,
    TooManyAttemptsError,
    UserInactiveError,
)
from app.domain.interfaces.i_token_store import ITokenStore
from app.domain.interfaces.i_user_repo import IUserRepo
from app.application.dto import TokenPairDTO
from app.application.services.token_service import TokenService


MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TTL         = 300  # 5 минут


@dataclass
class LoginUserCommand:
    email:    str
    password: str


class LoginUserHandler:

    def __init__(
        self,
        user_repo:    IUserRepo,
        token_store:  ITokenStore,
        token_service: TokenService,
    ) -> None:
        self.user_repo     = user_repo
        self.token_store   = token_store
        self.token_service = token_service

    async def handle(self, command: LoginUserCommand) -> TokenPairDTO:

        # 1. Проверка блокировки по количеству неудачных попыток
        attempts = await self.token_store.get_failed_attempts(command.email)
        if attempts >= MAX_FAILED_ATTEMPTS:
            raise TooManyAttemptsError()

        # 2. Ищем пользователя
        user = await self.user_repo.get_by_email(command.email)

        # 3. Проверяем пароль — одно исключение для обоих случаев
        #    (не даём понять атакующему существует ли email)
        if not user or not user.verify_password(command.password):
            await self.token_store.increment_failed_attempts(
                command.email,
                ttl=LOCKOUT_TTL,
            )
            raise InvalidCredentialsError()

        # 4. Проверяем активность аккаунта
        if not user.is_active:
            raise UserInactiveError()

        # 5. Сбрасываем счётчик после успешного логина
        await self.token_store.reset_failed_attempts(command.email)

        # 6. Выдаём токены
        return await self.token_service.create_token_pair(user, self.token_store)