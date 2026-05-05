from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.domain.entities import (
    AnalystRating,
    Company,
    FinancialMetrics,
    FinancialReport,
)
from app.domain.exceptions import CompanyNotFoundError, MetricsNotFoundError
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.domain.interfaces.i_financial_repo import IFinancialRepo
from app.domain.interfaces.i_valuation_model import IValuationModel
from app.domain.value_objects import ValuationResult


@dataclass
class CompanyReport:
    ticker: str
    company: Optional[Company] = None
    metrics: Optional[FinancialMetrics] = None
    reports: list[FinancialReport] = field(default_factory=list)
    valuations: list[ValuationResult] = field(default_factory=list)
    peers: list[FinancialMetrics] = field(default_factory=list)
    analyst_ratings: list[AnalystRating] = field(default_factory=list)


class CompanyReportBuilder:
    """
    Builder-паттерн для сборки финансового отчёта компании.

    Каждый with_*() метод регистрирует шаг.
    build() выполняет все независимые шаги параллельно через asyncio.gather.

    Пример использования:
        report = await (
            CompanyReportBuilder("AAPL", company_repo, financial_repo)
            .with_basic_info()
            .with_financial_metrics()
            .with_valuation(DCFModel())
            .with_peer_comparison()
            .with_analyst_ratings()
            .build()
        )
    """

    def __init__(
        self,
        ticker: str,
        company_repo: ICompanyRepo,
        financial_repo: IFinancialRepo,
        current_price: Decimal = Decimal("0"),
    ) -> None:
        self._ticker = ticker
        self._company_repo = company_repo
        self._financial_repo = financial_repo
        self._current_price = current_price

        self._include_basic_info = False
        self._include_metrics = False
        self._valuation_models: list[IValuationModel] = []
        self._include_peers = False
        self._include_ratings = False
        self._reports_limit = 8

    # ── Fluent API ───────────────────────────────────────────────────────────

    def with_basic_info(self) -> "CompanyReportBuilder":
        self._include_basic_info = True
        return self

    def with_financial_metrics(self) -> "CompanyReportBuilder":
        self._include_metrics = True
        return self

    def with_valuation(self, model: IValuationModel) -> "CompanyReportBuilder":
        self._valuation_models.append(model)
        return self

    def with_peer_comparison(self) -> "CompanyReportBuilder":
        self._include_peers = True
        return self

    def with_analyst_ratings(self) -> "CompanyReportBuilder":
        self._include_ratings = True
        return self

    def with_reports_limit(self, limit: int) -> "CompanyReportBuilder":
        self._reports_limit = limit
        return self

    # ── Build ────────────────────────────────────────────────────────────────

    async def build(self) -> CompanyReport:
        report = CompanyReport(ticker=self._ticker)

        # Сначала параллельно загружаем независимые данные
        tasks: dict[str, asyncio.coroutine] = {}

        if self._include_basic_info:
            tasks["company"] = self._company_repo.get_by_ticker(self._ticker)

        if self._include_metrics or self._valuation_models:
            tasks["metrics"] = self._financial_repo.get_metrics(self._ticker)
            tasks["reports"] = self._financial_repo.get_reports(
                self._ticker, limit=self._reports_limit
            )

        if self._include_ratings:
            tasks["ratings"] = self._financial_repo.get_analyst_ratings(self._ticker)

        if tasks:
            keys = list(tasks.keys())
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            resolved = dict(zip(keys, results))

            if "company" in resolved:
                company = resolved["company"]
                if isinstance(company, Exception):
                    raise company
                if company is None:
                    raise CompanyNotFoundError(self._ticker)
                report.company = company

            if "reports" in resolved:
                rep = resolved["reports"]
                report.reports = rep if not isinstance(rep, Exception) else []

            if "metrics" in resolved:
                met = resolved["metrics"]
                if isinstance(met, Exception):
                    raise met
                report.metrics = met

            if "ratings" in resolved:
                rat = resolved["ratings"]
                report.analyst_ratings = rat if not isinstance(rat, Exception) else []

        # Валюация требует отчётов и метрик — запускаем после
        if self._valuation_models and report.reports:
            metrics = report.metrics
            if metrics is None:
                raise MetricsNotFoundError(self._ticker)

            valuation_tasks = [
                model.estimate(
                    self._ticker,
                    report.reports,
                    metrics,
                    self._current_price,
                )
                for model in self._valuation_models
            ]
            val_results = await asyncio.gather(*valuation_tasks, return_exceptions=True)
            report.valuations = [
                r for r in val_results if not isinstance(r, Exception)
            ]

        # Peers: топ компаний того же сектора по screener
        if self._include_peers and report.metrics:
            sector = report.company.sector if report.company else None
            peers = await self._financial_repo.screen(
                sector=sector,
                limit=5,
                offset=0,
            )
            report.peers = [p for p in peers if p.ticker != self._ticker]

        return report
