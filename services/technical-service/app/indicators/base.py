import pandas as pd

from app.domain.interfaces.i_indicator import IIndicator
from app.domain.exceptions import InsufficientDataError


class BaseIndicator(IIndicator):
    """Базовый класс: валидация min_periods перед расчётом."""

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < self.min_periods:
            raise InsufficientDataError(self.indicator_type, self.min_periods, len(df))
        return self._calculate(df.copy())

    def _calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError