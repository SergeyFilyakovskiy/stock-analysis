from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 минут


class IndicatorCache:
    """
    Redis-кэш для результатов расчёта индикаторов.

    Ключ: "ta:{ticker}:{sorted_types}:{period}:{interval}"
    Пример: "ta:AAPL:macd,rsi:14:1d"

    TTL по умолчанию — 5 минут (переопределяется через config).
    """

    def __init__(self, redis: Redis, ttl: int = DEFAULT_TTL) -> None:
        self._redis = redis
        self._ttl   = ttl

    # ── публичное API ─────────────────────────────────────────────────────────

    async def get(self, key: str) -> Any | None:
        """Возвращает десериализованное значение или None при промахе."""
        try:
            raw = await self._redis.get(key)
        except Exception as exc:
            logger.warning("Cache GET error [%s]: %s", key, exc)
            return None

        if raw is None:
            return None

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Cache decode error for key %s", key)
            return None

    async def set(self, key: str, value: Any) -> None:
        """Сериализует value в JSON и сохраняет с TTL."""
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=self._ttl)
        except Exception as exc:
            # Ошибка кэша не должна ронять основной флоу
            logger.warning("Cache SET error [%s]: %s", key, exc)

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as exc:
            logger.warning("Cache DELETE error [%s]: %s", key, exc)

    # ── построение ключей ─────────────────────────────────────────────────────

    @staticmethod
    def make_indicators_key(
        ticker:   str,
        types:    list[str],
        period:   int,
        interval: str,
    ) -> str:
        """
        Детерминированный ключ: типы сортируются, чтобы
        "rsi,macd" и "macd,rsi" давали один и тот же ключ.
        """
        sorted_types = ",".join(sorted(t.lower() for t in types))
        return f"ta:{ticker.upper()}:{sorted_types}:{period}:{interval}"

    @staticmethod
    def make_signals_key(ticker: str, interval: str) -> str:
        return f"ta:signals:{ticker.upper()}:{interval}"

    @staticmethod
    def make_patterns_key(ticker: str, interval: str) -> str:
        return f"ta:patterns:{ticker.upper()}:{interval}"