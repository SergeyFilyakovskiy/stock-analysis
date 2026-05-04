from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone

from app.application.dto import SignalDto
from app.application.queries.get_indicators import GetIndicatorsQuery
from app.domain.value_objects import IndicatorType, SignalType
from app.grpc.client import MarketServiceClient
from app.infrastructure.cache.indicator_cache import IndicatorCache

logger = logging.getLogger(__name__)

# Все индикаторы участвуют в голосовании
_VOTING_INDICATORS = [
    IndicatorType.RSI,
    IndicatorType.MACD,
    IndicatorType.BOLLINGER,
]


class GetSignalsQuery:
    """
    Use-case: агрегированный торговый сигнал по тикеру.

    Голосование: каждый индикатор даёт BUY / SELL / NEUTRAL.
    Итоговый сигнал — большинство голосов.
    confidence = доля индикаторов проголосовавших за итог.
    """

    def __init__(self, cache: IndicatorCache, client: MarketServiceClient) -> None:
        self._cache    = cache
        self._client   = client
        self._ind_query = GetIndicatorsQuery(cache, client)

    async def execute(self, ticker: str, interval: str = "1d") -> SignalDto:
        cache_key = IndicatorCache.make_signals_key(ticker, interval)
        cached    = await self._cache.get(cache_key)
        if cached is not None:
            return SignalDto(**cached)

        ind_dto = await self._ind_query.execute(
            ticker   = ticker,
            types    = _VOTING_INDICATORS,
            period   = 14,
            interval = interval,
        )

        breakdown  = {r.indicator.value: r.signal.value for r in ind_dto.results}
        votes      = Counter(breakdown.values())
        top_signal = votes.most_common(1)[0][0] if votes else SignalType.NEUTRAL.value
        confidence = votes[top_signal] / len(breakdown) if breakdown else 0.0

        dto = SignalDto(
            ticker     = ticker,
            signal     = SignalType(top_signal),
            confidence = round(confidence, 2),
            breakdown  = breakdown,
            timestamp  = datetime.now(timezone.utc),
        )

        await self._cache.set(cache_key, {
            "ticker":     dto.ticker,
            "signal":     dto.signal.value,
            "confidence": dto.confidence,
            "breakdown":  dto.breakdown,
            "timestamp":  dto.timestamp.isoformat(),
        })
        return dto