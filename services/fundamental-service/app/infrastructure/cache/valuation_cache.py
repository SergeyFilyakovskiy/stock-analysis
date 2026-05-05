import json
from decimal import Decimal
from typing import Optional

from app.core.config import settings
from app.domain.value_objects import ValuationResult
from app.infrastructure.cache.redis_client import get_redis


class ValuationCache:
    """
    Кэширует результаты тяжёлых валюационных расчётов (DCF, PE, EV/EBITDA).
    TTL = 1 час (настраивается через settings.valuation_cache_ttl).
    Инвалидируется вручную при сохранении нового финансового отчёта.
    """

    _PREFIX = "valuation"

    @staticmethod
    def _key(ticker: str, model_name: str) -> str:
        return f"{ValuationCache._PREFIX}:{ticker}:{model_name}"

    async def get(self, ticker: str, model_name: str) -> Optional[ValuationResult]:
        redis = await get_redis()
        raw = await redis.get(self._key(ticker, model_name))
        if raw is None:
            return None
        data = json.loads(raw)
        return ValuationResult(
            ticker=data["ticker"],
            model_name=data["model_name"],
            estimated_value=Decimal(data["estimated_value"]),
            current_price=Decimal(data["current_price"]),
            confidence_score=data["confidence_score"],
        )

    async def set(self, result: ValuationResult) -> None:
        redis = await get_redis()
        data = {
            "ticker": result.ticker,
            "model_name": result.model_name,
            "estimated_value": str(result.estimated_value),
            "current_price": str(result.current_price),
            "confidence_score": result.confidence_score,
        }
        await redis.setex(
            self._key(result.ticker, result.model_name),
            settings.VALUATION_CACHE_TTL,
            json.dumps(data),
        )

    async def invalidate(self, ticker: str) -> None:
        """Сбрасываем кэш для всех моделей при появлении нового отчёта."""
        redis = await get_redis()
        pattern = f"{self._PREFIX}:{ticker}:*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
