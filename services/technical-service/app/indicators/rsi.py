import pandas as pd
import numpy as np
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
        

        close  = df["close"].astype(float).to_numpy()
        n      = self._period
        deltas = np.diff(close)                          # len = len(close) - 1

        # seed: SMA первых n дельт
        avg_gain = deltas[:n].clip(min=0).sum() / n
        avg_loss = (-deltas[:n]).clip(min=0).sum() / n

        rsi_values = np.full(len(close), np.nan)

        for i, d in enumerate(deltas[n:], start=n + 1):
            gain      = d if d > 0 else 0.0
            loss      = -d if d < 0 else 0.0
            avg_gain  = (avg_gain * (n - 1) + gain) / n
            avg_loss  = (avg_loss * (n - 1) + loss) / n
            rsi_values[i] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)

        df["rsi"] = np.round(rsi_values, 4)
        return df