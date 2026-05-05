from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities import Company, FinancialMetrics
from app.domain.exceptions import CompanyNotFoundError, MetricsNotFoundError
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.domain.interfaces.i_financial_repo import IFinancialRepo
from app.grpc_client.market_client import MarketServiceClient


@dataclass
class GetCompanyMetricsQuery:
    ticker: str


@dataclass
class CompanyMetricsResult:
    company: Company
    metrics: FinancialMetrics
    current_price: Decimal


class GetCompanyMetricsHandler:

    def __init__(
        self,
        company_repo: ICompanyRepo,
        financial_repo: IFinancialRepo,
        market_client: MarketServiceClient,
    ) -> None:
        self._company_repo = company_repo
        self._financial_repo = financial_repo
        self._market_client = market_client

    async def handle(self, query: GetCompanyMetricsQuery) -> CompanyMetricsResult:
        import asyncio

        ticker = query.ticker.upper()
        company, metrics, price = await asyncio.gather(
            self._company_repo.get_by_ticker(ticker),
            self._financial_repo.get_metrics(ticker),
            self._market_client.get_last_price(ticker),
            return_exceptions=True,
        )

        if company is None or isinstance(company, Exception):
            raise CompanyNotFoundError(ticker)
        if metrics is None or isinstance(metrics, Exception):
            raise MetricsNotFoundError(ticker)

        current_price = price if isinstance(price, Decimal) else Decimal("0")

        return CompanyMetricsResult(
            company=company,
            metrics=metrics,
            current_price=current_price,
        )
