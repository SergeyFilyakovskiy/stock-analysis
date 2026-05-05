from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from app.domain.entities import FinancialReport


class BaseFinancialProvider(ABC):
    """Абстрактный провайдер финансовых данных."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def get_financials(
        self,
        ticker: str,
        limit: int = 8,
        period_type: str = "annual",   # "annual" | "quarterly"
    ) -> list[FinancialReport]:
        """Получить финансовые отчёты из внешнего API."""
        ...

    @abstractmethod
    async def get_company_details(self, ticker: str) -> dict:
        """Получить базовую информацию о компании."""
        ...
