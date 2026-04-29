from __future__ import annotations
from dataclasses import dataclass, field
import bcrypt
import re

@dataclass(frozen=True)
class Email:
    
    value: str

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise TypeError("Email must be a sting")
        normalized = self.value.strip().lower()
        if not re.match(r'^[\w.+-]+@[\w-]+\.[a-z]{2,}$', normalized):
            raise ValueError(f"Incorrect email format: {self.value}")
        object.__setattr__(self, 'value', normalized)

    def __str__(self) -> str:
        return self.value
    
@dataclass(frozen=True)
class HashedPassword:

    password: str

    @staticmethod
    def from_plain(plain: str) -> HashedPassword:
        """Создание из открытого пароля"""

        if len(plain)<8:
            raise ValueError("Password must be at least 8 characters")
        if len(plain)>128:
            raise ValueError("Password is too long")
        hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt())
        return HashedPassword(hashed.decode())
        
    @staticmethod
    def from_hashed(hashed: str)-> HashedPassword:
        return HashedPassword(hashed)
    
    def verify(self, plain: str)-> bool:
        return bcrypt.checkpw(plain.encode(), self.password.encode())
    
    def __repr__(self) -> str:
        return "HashedPassword"
    
@dataclass(frozen=True)
class Role:

    value: str

    ADMIN = 'admin'
    USER = 'user'
    ALLOWED_ROLES = {USER, ADMIN}

    def __post_init__(self):
        if self.value not in self.ALLOWED_ROLES:
            raise ValueError("Invalid role: {self.value}. Allowed: {self.ALLOWED}")
        
    def is_admin(self) -> bool:
        return self.value == self.ADMIN
    
    def __str__(self)-> str:
        return self.value
    
@dataclass
class UserProfile:
    """value-object для сущности User"""
    
    first_name: str
    last_name: str
    avatar_url: str | None = None
    bio: str | None = None

    def update(self, **kwargs)-> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                object.__setattr__(self, key, value)

