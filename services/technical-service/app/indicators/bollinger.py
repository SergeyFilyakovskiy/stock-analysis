import pandas as pd

from app.indicators.base import BaseIndicator
from app.domain.value_objects import IndicatorType


class BollingerBandsIndicator(BaseIndicator):
    """
    Bollinger Bands.
    Добавляет колонки: bb_upper, bb_middle, bb_lower, bb_width, bb_%b
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0) -> None:
        self._period  = period
        self._std_dev = std_dev

    @property
    def min_periods(self) -> int:
        return self._period

    @property
    def indicator_type(self) -> str:
        return IndicatorType.BOLLINGER.value

    def _calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        close  = df["close"].astype(float)
        middle = close.rolling(self._period).mean()
        std    = close.rolling(self._period).std(ddof=0)

        upper = middle + self._std_dev * std
        lower = middle - self._std_dev * std

        df["bb_upper"]  = upper.round(4)
        df["bb_middle"] = middle.round(4)
        df["bb_lower"]  = lower.round(4)
        df["bb_width"]  = ((upper - lower) / middle).round(6)   # нормализованная ширина
        df["bb_%b"]     = ((close - lower) / (upper - lower)).round(6)  # позиция цены
        return df