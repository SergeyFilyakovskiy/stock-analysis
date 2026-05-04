from abc import ABC, abstractmethod

import pandas as pd


class IIndicator(ABC):
    """
    Контракт для всех индикаторов технического анализа.

    Каждый индикатор получает DataFrame с колонками
    [time, open, high, low, close, volume] и обогащает его
    новыми колонками, специфичными для данного индикатора.
    """

    @abstractmethod
    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Принимает OHLCV DataFrame, возвращает его копию
        с добавленными колонками индикатора.
        Не мутирует входной DataFrame.
        """
        ...

    @property
    @abstractmethod
    def min_periods(self) -> int:
        """Минимальное количество свечей для расчёта."""
        ...

    @property
    @abstractmethod
    def indicator_type(self) -> str:
        """Строковое имя индикатора (совпадает с IndicatorType.value)."""
        ...