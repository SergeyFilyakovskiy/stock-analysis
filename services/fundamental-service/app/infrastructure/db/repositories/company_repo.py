from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Company
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.infrastructure.db.models import CompanyModel


class CompanyRepo(ICompanyRepo):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_ticker(self, ticker: str) -> Optional[Company]:
        result = await self._session.execute(
            select(CompanyModel).where(CompanyModel.ticker == ticker)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save(self, company: Company) -> None:
        result = await self._session.execute(
            select(CompanyModel).where(CompanyModel.ticker == company.ticker)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = CompanyModel()
            self._session.add(row)
        self._update_model(row, company)

    async def exists(self, ticker: str) -> bool:
        result = await self._session.execute(
            select(CompanyModel.ticker).where(CompanyModel.ticker == ticker)
        )
        return result.scalar_one_or_none() is not None

    async def get_all_tickers(self) -> list[str]:
        result = await self._session.execute(select(CompanyModel.ticker))
        return list(result.scalars().all())

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(m: CompanyModel) -> Company:
        return Company(
            ticker=m.ticker,
            name=m.name,
            sector=m.sector,
            industry=m.industry,
            market_cap=m.market_cap,
            country=m.country,
            description=m.description,
        )

    @staticmethod
    def _update_model(m: CompanyModel, e: Company) -> None:
        m.ticker = e.ticker
        m.name = e.name
        m.sector = e.sector
        m.industry = e.industry
        m.market_cap = e.market_cap
        m.country = e.country
        m.description = e.description
