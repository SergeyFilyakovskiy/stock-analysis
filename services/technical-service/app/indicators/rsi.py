import pandas as pd

from app.indicators.base import BaseIndicator
from app.domain.value_objects import IndicatorType


class RSIIndicator(BaseIndicator):
    """
    Relative Strength Index (Wilder EMA).
    Добавляет колонку: rsi
    """

    def __init__(self, period: int = 14) -> None:
        self._period = period

    @property
    def min_periods(self) -> int:
        return self._period + 1

    @property
    def indicator_type(self) -> str:
        return IndicatorType.RSI.value

    def _calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df["close"].astype(float).diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)

        avg_gain = gain.ewm(alpha=1 / self._period, min_periods=self._period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self._period, min_periods=self._period, adjust=False).mean()

        rs        = avg_gain / avg_loss.replace(0, float("inf"))
        df["rsi"] = (100 - (100 / (1 + rs))).round(4)
        return df
