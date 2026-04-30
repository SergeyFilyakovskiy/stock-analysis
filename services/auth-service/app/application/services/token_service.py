from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, exceptions


from app.application.dto import TokenPairDTO
from app.core.config import settings
from app.domain.entities import User
from app.domain.exceptions import InvalidTokenError
from app.domain.interfaces.i_token_store import ITokenStore


class TokenService:

    def create_access_token(self, user: User) -> tuple[str, str]:
        """Возвращает (token, jti)"""
        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        payload = {
            "sub":   str(user.id),
            "email": user.email.value,
            "role":  user.role.value,
            "type":  "access",
            "jti":   jti,
            "iat":   now,
            "exp":   now + timedelta(seconds=settings.jwt_access_expire),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )
        return token, jti

    def create_refresh_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub":  str(user.id),
            "type": "refresh",
            "iat":  now,
            "exp":  now + timedelta(seconds=settings.jwt_refresh_expire),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.jwt_secret.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
        except exceptions.ExpiredSignatureError:
            raise InvalidTokenError("Token expired")
        except exceptions.JWTError:
            raise InvalidTokenError("Invalid token")

    async def create_token_pair(
        self,
        user: User,
        token_store: ITokenStore,
    ) -> TokenPairDTO:
        access_token, jti    = self.create_access_token(user)
        refresh_token        = self.create_refresh_token(user)

        # Сохраняем refresh token в Redis
        await token_store.save_refresh_token(
            user.id,
            refresh_token,
            ttl=settings.jwt_refresh_expire,
        )

        return TokenPairDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )