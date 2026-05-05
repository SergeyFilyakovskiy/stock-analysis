from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.entities import FinancialReport, FinancialMetrics
from app.domain.value_objects import ValuationResult


class IValuationModel(ABC):
    """Strategy-интерфейс для моделей оценки стоимости компании."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Человекочитаемое название модели."""

    @abstractmethod
    async def estimate(
        self,
        ticker: str,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
        current_price: Decimal,
    ) -> ValuationResult:
        """
        Рассчитывает справедливую стоимость акции.

        Raises:
            InsufficientDataError: если не хватает данных для расчёта.
            ValuationError: при любой другой ошибке модели.
        """

    @abstractmethod
    def confidence_score(
        self,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
    ) -> float:
        """
        Возвращает оценку надёжности результата от 0.0 до 1.0.
        Зависит от полноты и качества входных данных.
        """