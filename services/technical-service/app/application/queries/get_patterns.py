from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import pandas as pd

from app.application.dto import CandlePatternDto
from app.domain.value_objects import SignalType
from app.grpc.client import MarketServiceClient
from app.infrastructure.cache.indicator_cache import IndicatorCache

logger = logging.getLogger(__name__)


class GetPatternsQuery:
    """
    Use-case: поиск паттернов японских свечей.

    Реализованы базовые паттерны без внешних библиотек:
    Doji, Hammer, Shooting Star, Bullish/Bearish Engulfing.
    """

    def __init__(self, cache: IndicatorCache, client: MarketServiceClient) -> None:
        self._cache  = cache
        self._client = client

    async def execute(self, ticker: str, interval: str = "1d") -> list[CandlePatternDto]:
        cache_key = IndicatorCache.make_patterns_key(ticker, interval)
        cached    = await self._cache.get(cache_key)
        if cached is not None:
            return [CandlePatternDto(**p) for p in cached]

        to_dt   = datetime.now(timezone.utc)
        from_dt = to_dt - timedelta(days=60)

        async with self._client as client:
            ohlcv = await client.get_ohlcv(ticker, interval, from_dt, to_dt)

        if not ohlcv.bars:
            return []

        df = pd.DataFrame([
            {
                "time":  b.time,
                "open":  float(b.open)  if b.open  else None,
                "high":  float(b.high)  if b.high  else None,
                "low":   float(b.low)   if b.low   else None,
                "close": float(b.close),
            }
            for b in ohlcv.bars
        ]).dropna()

        patterns = self._detect(df, ticker)

        await self._cache.set(cache_key, [
            {
                "ticker":      p.ticker,
                "time":        p.time.isoformat(),
                "pattern":     p.pattern,
                "direction":   p.direction.value,
                "description": p.description,
            }
            for p in patterns
        ])
        return patterns

    # ── детекторы ─────────────────────────────────────────────────────────────

    @staticmethod
    def _detect(df: pd.DataFrame, ticker: str) -> list[CandlePatternDto]:
        results: list[CandlePatternDto] = []

        for i in range(1, len(df)):
            cur  = df.iloc[i]
            prev = df.iloc[i - 1]

            body      = abs(cur["close"] - cur["open"])
            candle_rng = cur["high"] - cur["low"]
            if candle_rng == 0:
                continue

            # Doji — тело < 5% от диапазона
            if body / candle_rng < 0.05:
                results.append(CandlePatternDto(
                    ticker      = ticker,
                    time        = cur["time"],
                    pattern     = "doji",
                    direction   = SignalType.NEUTRAL,
                    description = "Indecision candle",
                ))
                continue

            lower_shadow = cur["open"] - cur["low"] if cur["close"] >= cur["open"] else cur["close"] - cur["low"]
            upper_shadow = cur["high"] - cur["close"] if cur["close"] >= cur["open"] else cur["high"] - cur["open"]

            # Hammer — длинная нижняя тень ≥ 2× тела, малая верхняя
            if lower_shadow >= 2 * body and upper_shadow < body:
                results.append(CandlePatternDto(
                    ticker      = ticker,
                    time        = cur["time"],
                    pattern     = "hammer",
                    direction   = SignalType.BUY,
                    description = "Potential reversal up",
                ))
                continue

            # Shooting Star — длинная верхняя тень ≥ 2× тела, малая нижняя
            if upper_shadow >= 2 * body and lower_shadow < body:
                results.append(CandlePatternDto(
                    ticker      = ticker,
                    time        = cur["time"],
                    pattern     = "shooting_star",
                    direction   = SignalType.SELL,
                    description = "Potential reversal down",
                ))
                continue

            # Bullish Engulfing
            if (
                prev["close"] < prev["open"]
                and cur["close"] > cur["open"]
                and cur["open"]  < prev["close"]
                and cur["close"] > prev["open"]
            ):
                results.append(CandlePatternDto(
                    ticker      = ticker,
                    time        = cur["time"],
                    pattern     = "bullish_engulfing",
                    direction   = SignalType.BUY,
                    description = "Bullish reversal signal",
                ))
                continue

            # Bearish Engulfing
            if (
                prev["close"] > prev["open"]
                and cur["close"] < cur["open"]
                and cur["open"]  > prev["close"]
                and cur["close"] < prev["open"]
            ):
                results.append(CandlePatternDto(
                    ticker      = ticker,
                    time        = cur["time"],
                    pattern     = "bearish_engulfing",
                    direction   = SignalType.SELL,
                    description = "Bearish reversal signal",
                ))

        return results