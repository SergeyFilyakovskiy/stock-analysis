from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import FinancialReport, FinancialMetrics, AnalystRating


class IFinancialRepo(ABC):

    # ── Financial Reports ────────────────────────────────────────────────────
    @abstractmethod
    async def get_reports(
        self,
        ticker: str,
        limit: int = 8,
        period_type: Optional[str] = None,  # "quarterly" | "annual"
    ) -> list[FinancialReport]:
        ...

    @abstractmethod
    async def get_report(
        self, ticker: str, period: str
    ) -> Optional[FinancialReport]:
        ...

    @abstractmethod
    async def save_report(self, report: FinancialReport) -> None:
        ...

    @abstractmethod
    async def save_reports(self, reports: list[FinancialReport]) -> None:
        ...

    # ── Financial Metrics ────────────────────────────────────────────────────
    @abstractmethod
    async def get_metrics(self, ticker: str) -> Optional[FinancialMetrics]:
        ...

    @abstractmethod
    async def save_metrics(self, metrics: FinancialMetrics) -> None:
        ...

    # ── Analyst Ratings ──────────────────────────────────────────────────────
    @abstractmethod
    async def get_analyst_ratings(
        self, ticker: str, limit: int = 10
    ) -> list[AnalystRating]:
        ...

    @abstractmethod
    async def save_analyst_rating(self, rating: AnalystRating) -> None:
        ...

    # ── Screener ─────────────────────────────────────────────────────────────
    @abstractmethod
    async def screen(
        self,
        pe_max: Optional[float] = None,
        pe_min: Optional[float] = None,
        roe_min: Optional[float] = None,
        ev_ebitda_max: Optional[float] = None,
        debt_equity_max: Optional[float] = None,
        sector: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialMetrics]:
        ...