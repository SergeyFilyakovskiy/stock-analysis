from dataclasses import dataclass
from typing import Optional

from app.domain.entities import FinancialReport
from app.domain.exceptions import CompanyNotFoundError
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.domain.interfaces.i_financial_repo import IFinancialRepo


@dataclass
class GetFinancialReportsQuery:
    ticker: str
    limit: int = 8
    period_type: Optional[str] = None  # "annual" | "quarterly"


class GetFinancialReportsHandler:

    def __init__(
        self,
        company_repo: ICompanyRepo,
        financial_repo: IFinancialRepo,
    ) -> None:
        self._company_repo = company_repo
        self._financial_repo = financial_repo

    async def handle(self, query: GetFinancialReportsQuery) -> list[FinancialReport]:
        ticker = query.ticker.upper()
        if not await self._company_repo.exists(ticker):
            raise CompanyNotFoundError(ticker)
        return await self._financial_repo.get_reports(
            ticker, limit=query.limit, period_type=query.period_type
        )
