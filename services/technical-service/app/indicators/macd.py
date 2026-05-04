import pandas as pd

from app.indicators.base import BaseIndicator
from app.domain.value_objects import IndicatorType


class MACDIndicator(BaseIndicator):
    """
    Moving Average Convergence Divergence.
    Добавляет колонки: macd, macd_signal, macd_hist
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self._fast   = fast
        self._slow   = slow
        self._signal = signal

    @property
    def min_periods(self) -> int:
        return self._slow + self._signal

    @property
    def indicator_type(self) -> str:
        return IndicatorType.MACD.value

    def _calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["close"].astype(float)

        ema_fast = close.ewm(span=self._fast, adjust=False).mean()
        ema_slow = close.ewm(span=self._slow, adjust=False).mean()

        df["macd"]       = (ema_fast - ema_slow).round(4)
        df["macd_signal"] = df["macd"].ewm(span=self._signal, adjust=False).mean().round(4)
        df["macd_hist"]  = (df["macd"] - df["macd_signal"]).round(4)
        return df
