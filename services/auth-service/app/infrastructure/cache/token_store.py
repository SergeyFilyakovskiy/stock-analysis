from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis

from app.domain.interfaces.i_token_store import ITokenStore


class RedisTokenStore(ITokenStore):

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    # ── Ключи ─────────────────────────────────────────────

    @staticmethod
    def _refresh_key(user_id: UUID) -> str:
        return f"auth:refresh:{user_id}"

    @staticmethod
    def _blacklist_key(jti: str) -> str:
        return f"auth:blacklist:{jti}"

    @staticmethod
    def _failed_attempts_key(email: str) -> str:
        return f"auth:failed:{email.lower()}"

    # ── Refresh tokens ────────────────────────────────────

    async def save_refresh_token(
        self,
        user_id: UUID,
        token: str,
        ttl: int,
    ) -> None:
        await self.redis.set(
            self._refresh_key(user_id),
            token,
            ex=ttl,
        )

    async def get_refresh_token(self, user_id: UUID) -> str | None:
        value = await self.redis.get(self._refresh_key(user_id))
        return value.decode() if value else None

    async def delete_refresh_token(self, user_id: UUID) -> None:
        await self.redis.delete(self._refresh_key(user_id))

    async def refresh_token_exists(self, user_id: UUID, token: str) -> bool:
        """Защита от replay-атаки — токен должен совпадать с сохранённым"""
        stored = await self.get_refresh_token(user_id)
        return stored is not None and stored == token

    # ── Blacklist access tokens ───────────────────────────

    async def blacklist_token(self, jti: str, ttl: int) -> None:
        """
        TTL = оставшееся время жизни access token.
        Когда токен протухнет — Redis сам удалит запись из blacklist.
        """
        await self.redis.set(
            self._blacklist_key(jti),
            "1",
            ex=ttl,
        )

    async def is_blacklisted(self, jti: str) -> bool:
        return await self.redis.exists(self._blacklist_key(jti)) > 0

    # ── Failed login attempts ─────────────────────────────

    async def increment_failed_attempts(self, email: str, ttl: int) -> int:
        key = self._failed_attempts_key(email)
        count = await self.redis.incr(key)
        if count == 1:
            # Устанавливаем TTL только при первой попытке
            await self.redis.expire(key, ttl)
        return count

    async def get_failed_attempts(self, email: str) -> int:
        value = await self.redis.get(self._failed_attempts_key(email))
        return int(value) if value else 0

    async def reset_failed_attempts(self, email: str) -> None:
        await self.redis.delete(self._failed_attempts_key(email))