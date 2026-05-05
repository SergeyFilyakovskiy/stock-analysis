import asyncio
from dataclasses import dataclass
from decimal import Decimal

from app.builders.company_report_builder import CompanyReport, CompanyReportBuilder
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.domain.interfaces.i_financial_repo import IFinancialRepo
from app.grpc_client.market_client import MarketServiceClient
from app.valuation.dcf import DCFModel
from app.valuation.pe_relative import PERelativeModel


@dataclass
class CompareCompaniesQuery:
    tickers: list[str]
    include_valuation: bool = True


class CompareCompaniesHandler:

    def __init__(
        self,
        company_repo: ICompanyRepo,
        financial_repo: IFinancialRepo,
        market_client: MarketServiceClient,
    ) -> None:
        self._company_repo = company_repo
        self._financial_repo = financial_repo
        self._market_client = market_client

    async def handle(self, query: CompareCompaniesQuery) -> list[CompanyReport]:
        prices = await asyncio.gather(
            *[self._market_client.get_last_price(t) for t in query.tickers],
            return_exceptions=True,
        )

        tasks = []
        for ticker, price in zip(query.tickers, prices):
            current_price = price if isinstance(price, Decimal) else Decimal("0")
            builder = (
                CompanyReportBuilder(ticker, self._company_repo, self._financial_repo, current_price)
                .with_basic_info()
                .with_financial_metrics()
            )
            if query.include_valuation:
                builder = builder.with_valuation(DCFModel()).with_valuation(PERelativeModel())
            tasks.append(builder.build())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
