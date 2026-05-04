from __future__ import annotations

from typing import Type

from app.domain.interfaces.i_indicator import IIndicator
from app.domain.exceptions import UnknownIndicatorError


class IndicatorFactory:
    """
    Реестр индикаторов с декоратором @IndicatorFactory.register("rsi").
    Новый индикатор добавляется без правки этого файла.
    """

    _registry: dict[str, Type[IIndicator]] = {}

    @classmethod
    def register(cls, name: str):
        """Декоратор для регистрации класса индикатора по имени."""
        def decorator(klass: Type[IIndicator]) -> Type[IIndicator]:
            cls._registry[name.lower()] = klass
            return klass
        return decorator

    @classmethod
    def create(cls, indicator_type: str, params: dict | None = None) -> IIndicator:
        key = indicator_type.lower()
        if key not in cls._registry:
            raise UnknownIndicatorError(indicator_type)
        return cls._registry[key](**(params or {}))

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._registry.keys())


# ── Авторегистрация всех индикаторов ──────────────────────────────────────────
# Импорт здесь гарантирует, что декораторы @register отработают при старте.

from app.indicators.rsi       import RSIIndicator        # noqa: E402, F401
from app.indicators.macd      import MACDIndicator       # noqa: E402, F401
from app.indicators.bollinger  import BollingerBandsIndicator  # noqa: E402, F401
from app.indicators.sma       import SMAIndicator        # noqa: E402, F401
from app.indicators.ema       import EMAIndicator        # noqa: E402, F401

IndicatorFactory.register("rsi")(RSIIndicator)
IndicatorFactory.register("macd")(MACDIndicator)
IndicatorFactory.register("bollinger")(BollingerBandsIndicator)
IndicatorFactory.register("sma")(SMAIndicator)
IndicatorFactory.register("ema")(EMAIndicator)