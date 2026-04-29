# app/domain/entities.py
from dataclasses import dataclass, field
from uuid import UUID
from app.domain.value_objects import Email, Role, HashedPassword

@dataclass
class User:
    id: UUID
    email: Email
    role: Role
    hashed_password: HashedPassword | None = None

    def change_email(self, new_email: str) -> None:
        object.__setattr__(self, 'email', Email(new_email))

    def verify_password(self, plain: str) -> bool:
        if self.hashed_password is None:
            return False
        return self.hashed_password.verify(plain)

    def is_admin(self) -> bool:
        return self.role.is_admin()