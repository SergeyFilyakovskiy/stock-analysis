import pandas as pd

from app.indicators.base import BaseIndicator
from app.domain.value_objects import IndicatorType


class EMAIndicator(BaseIndicator):
    """
    Exponential Moving Average.
    Добавляет колонку: ema_{period}
    """

    def __init__(self, period: int = 20) -> None:
        self._period = period

    @property
    def min_periods(self) -> int:
        return self._period

    @property
    def indicator_type(self) -> str:
        return IndicatorType.EMA.value

    def _calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        col = f"ema_{self._period}"
        df[col] = df["close"].astype(float).ewm(span=self._period, adjust=False).mean().round(4)
        return df