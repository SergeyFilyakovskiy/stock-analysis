from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.domain.entities import User, UserProfile
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.interfaces.i_user_repo import IUserRepo
from app.domain.value_objects import Email, HashedPassword, Role


@dataclass
class RegisterUserCommand:
    email:    str
    password: str
    first_name: str | None = None
    last_name:  str | None = None


class RegisterUserHandler:

    def __init__(self, user_repo: IUserRepo) -> None:
        self.user_repo = user_repo

    async def handle(self, command: RegisterUserCommand) -> User:

        # 1. Валидация через value objects — если невалидно, сразу исключение
        email_vo    = Email(command.email)
        password_vo = HashedPassword.from_plain(command.password)

        # 2. Проверка что пользователь не существует
        if await self.user_repo.exists_by_email(email_vo.value):
            raise UserAlreadyExistsError(email_vo.value)

        # 3. Создаём доменный объект
        user = User(
            id=uuid.uuid4(),
            email=email_vo,
            hashed_password=password_vo,
            role=Role(Role.USER),
            is_active=True,
            is_verified=False,
            profile=UserProfile(
                first_name=command.first_name,
                last_name=command.last_name,
            ),
        )

        # 4. Сохраняем
        await self.user_repo.save(user)

        return user