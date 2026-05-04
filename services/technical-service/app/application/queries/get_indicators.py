from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pandas as pd

from app.application.dto import IndicatorResultDto, IndicatorsResponseDto
from app.core.config import settings
from app.domain.exceptions import InsufficientDataError
from app.domain.value_objects import IndicatorType, SignalType
from app.grpc.client import MarketServiceClient
from app.indicators.factory import IndicatorFactory
from app.indicators.pipeline import IndicatorPipeline
from app.infrastructure.cache.indicator_cache import IndicatorCache

logger = logging.getLogger(__name__)

# Минимальное количество свечей в запросе к market-service
_MIN_BARS = 200


def _infer_signal(indicator_type: str, df: pd.DataFrame) -> SignalType:
    """Простая эвристика сигнала по последней строке DataFrame."""
    last = df.iloc[-1]

    if indicator_type == IndicatorType.RSI.value:
        rsi = last.get("rsi")
        if rsi is None:
            return SignalType.NEUTRAL
        if rsi < 30:
            return SignalType.BUY
        if rsi > 70:
            return SignalType.SELL
        return SignalType.NEUTRAL

    if indicator_type == IndicatorType.MACD.value:
        hist = last.get("macd_hist")
        if hist is None:
            return SignalType.NEUTRAL
        if hist > 0:
            return SignalType.BUY
        if hist < 0:
            return SignalType.SELL
        return SignalType.NEUTRAL

    if indicator_type == IndicatorType.BOLLINGER.value:
        pct_b = last.get("bb_%b")
        if pct_b is None:
            return SignalType.NEUTRAL
        if pct_b < 0:
            return SignalType.BUY
        if pct_b > 1:
            return SignalType.SELL
        return SignalType.NEUTRAL

    # SMA / EMA — цена выше средней = бычий сигнал
    close = float(last["close"])
    for col in df.columns:
        if col.startswith(indicator_type):
            val = last.get(col)
            if val is not None:
                return SignalType.BUY if close > float(val) else SignalType.SELL

    return SignalType.NEUTRAL


class GetIndicatorsQuery:
    """
    Use-case: получить значения индикаторов для тикера.

    Флоу:
        1. Проверить кэш → вернуть если есть
        2. Запросить OHLCV у market-service через gRPC
        3. Прогнать через IndicatorPipeline
        4. Сохранить результат в кэш
        5. Вернуть IndicatorsResponseDto
    """

    def __init__(self, cache: IndicatorCache, client: MarketServiceClient) -> None:
        self._cache  = cache
        self._client = client

    async def execute(
        self,
        ticker:   str,
        types:    list[IndicatorType],
        period:   int,
        interval: str,
    ) -> IndicatorsResponseDto:
        type_values = [t.value for t in types]

        # 1. Кэш
        cache_key = IndicatorCache.make_indicators_key(ticker, type_values, period, interval)
        cached    = await self._cache.get(cache_key)
        if cached is not None:
            return self._deserialize(cached)

        # 2. OHLCV из market-service
        to_dt   = datetime.now(timezone.utc)
        from_dt = to_dt - timedelta(days=_bars_lookback(interval))

        async with self._client as client:
            ohlcv = await client.get_ohlcv(ticker, interval, from_dt, to_dt)

        if not ohlcv.bars:
            return IndicatorsResponseDto(ticker=ticker, interval=interval, results=())

        # 3. DataFrame → Pipeline
        df = pd.DataFrame([
            {
                "time":   b.time,
                "open":   float(b.open)   if b.open   else None,
                "high":   float(b.high)   if b.high   else None,
                "low":    float(b.low)    if b.low    else None,
                "close":  float(b.close),
                "volume": b.volume,
            }
            for b in ohlcv.bars
        ])

        indicators = [
            IndicatorFactory.create(t, {"period": period} if t in ("rsi", "sma", "ema") else {})
            for t in type_values
        ]
        pipeline = IndicatorPipeline(indicators)
        enriched = pipeline.calculate(df)

        # 4. Собираем результаты из последней строки
        last = enriched.iloc[-1]
        results: list[IndicatorResultDto] = []

        for ind_type in type_values:
            value = _extract_primary_value(ind_type, last)
            if value is None:
                continue
            results.append(IndicatorResultDto(
                ticker    = ticker,
                time      = last["time"],
                indicator = IndicatorType(ind_type),
                value     = Decimal(str(round(value, 4))),
                signal    = _infer_signal(ind_type, enriched),
            ))

        dto = IndicatorsResponseDto(
            ticker   = ticker,
            interval = interval,
            results  = tuple(results),
        )

        # 5. Кэш
        await self._cache.set(cache_key, self._serialize(dto))
        return dto

    # ── сериализация для кэша ─────────────────────────────────────────────────

    @staticmethod
    def _serialize(dto: IndicatorsResponseDto) -> dict:
        return {
            "ticker":   dto.ticker,
            "interval": dto.interval,
            "results": [
                {
                    "ticker":    r.ticker,
                    "time":      r.time.isoformat(),
                    "indicator": r.indicator.value,
                    "value":     str(r.value),
                    "signal":    r.signal.value,
                }
                for r in dto.results
            ],
        }

    @staticmethod
    def _deserialize(data: dict) -> IndicatorsResponseDto:
        return IndicatorsResponseDto(
            ticker   = data["ticker"],
            interval = data["interval"],
            results  = tuple(
                IndicatorResultDto(
                    ticker    = r["ticker"],
                    time      = datetime.fromisoformat(r["time"]),
                    indicator = IndicatorType(r["indicator"]),
                    value     = Decimal(r["value"]),
                    signal    = SignalType(r["signal"]),
                )
                for r in data["results"]
            ),
        )


def _bars_lookback(interval: str) -> int:
    """Сколько дней истории запрашивать под нужный интервал."""
    return {"1m": 1, "5m": 3, "1h": 30, "1d": 365}.get(interval, 30)


def _extract_primary_value(indicator_type: str, row: pd.Series) -> float | None:
    """Берёт главное значение индикатора из строки DataFrame."""
    mapping = {
        "rsi":       "rsi",
        "macd":      "macd",
        "bollinger": "bb_middle",
    }
    if indicator_type in mapping:
        val = row.get(mapping[indicator_type])
        return float(val) if val is not None and not pd.isna(val) else None

    # sma / ema — ищем колонку по префиксу
    for col in row.index:
        if col.startswith(indicator_type):
            val = row[col]
            return float(val) if val is not None and not pd.isna(val) else None

    return None