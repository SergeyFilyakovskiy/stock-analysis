from functools import reduce

import pandas as pd

from app.domain.interfaces.i_indicator import IIndicator


class IndicatorPipeline:
    """
    Последовательно применяет список индикаторов к DataFrame.
    Каждый индикатор обогащает DataFrame новыми колонками.
    При ошибке одного индикатора — пропускает и логирует, не роняет весь pipeline.
    """

    def __init__(self, indicators: list[IIndicator]) -> None:
        self._indicators = indicators

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        import logging
        logger = logging.getLogger(__name__)

        result = df.copy()
        for indicator in self._indicators:
            try:
                result = indicator.enrich(result)
            except Exception as exc:
                logger.warning(
                    "Indicator %s failed: %s",
                    indicator.indicator_type,
                    exc,
                    exc_info=True,
                )
        return result