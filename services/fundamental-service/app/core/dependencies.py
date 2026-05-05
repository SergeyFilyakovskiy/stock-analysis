from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.queries.compare_companies import CompareCompaniesHandler
from app.application.queries.get_company_metrics import GetCompanyMetricsHandler
from app.application.queries.get_financial_reports import GetFinancialReportsHandler
from app.application.queries.run_screener import RunScreenerHandler
from app.grpc_client.market_client import MarketServiceClient
from app.infrastructure.db.repositories.company_repo import CompanyRepo
from app.infrastructure.db.repositories.financial_repo import FinancialRepo
from app.infrastructure.db.session import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_company_metrics_handler(
    session: AsyncSession = Depends(get_db_session),
) -> GetCompanyMetricsHandler:
    return GetCompanyMetricsHandler(
        company_repo=CompanyRepo(session),
        financial_repo=FinancialRepo(session),
        market_client=MarketServiceClient(),
    )


async def get_financial_reports_handler(
    session: AsyncSession = Depends(get_db_session),
) -> GetFinancialReportsHandler:
    return GetFinancialReportsHandler(
        company_repo=CompanyRepo(session),
        financial_repo=FinancialRepo(session),
    )


async def get_screener_handler(
    session: AsyncSession = Depends(get_db_session),
) -> RunScreenerHandler:
    return RunScreenerHandler(financial_repo=FinancialRepo(session))


async def get_compare_handler(
    session: AsyncSession = Depends(get_db_session),
) -> CompareCompaniesHandler:
    return CompareCompaniesHandler(
        company_repo=CompanyRepo(session),
        financial_repo=FinancialRepo(session),
        market_client=MarketServiceClient(),
    )


def get_report_builder(session: AsyncSession = Depends(get_db_session)):
    """Возвращает фабрику билдеров (callable) с уже инжектированным session."""
    from app.builders.company_report_builder import CompanyReportBuilder

    def _factory(ticker: str):
        return CompanyReportBuilder(
            ticker=ticker,
            company_repo=CompanyRepo(session),
            financial_repo=FinancialRepo(session),
        )
    return _factory
