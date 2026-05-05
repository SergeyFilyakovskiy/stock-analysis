from dataclasses import dataclass, field
from typing import Optional

from app.domain.entities import FinancialMetrics
from app.domain.interfaces.i_financial_repo import IFinancialRepo


@dataclass
class ScreenerQuery:
    pe_max: Optional[float] = None
    pe_min: Optional[float] = None
    roe_min: Optional[float] = None
    ev_ebitda_max: Optional[float] = None
    debt_equity_max: Optional[float] = None
    sector: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class ScreenerResult:
    items: list[FinancialMetrics]
    total: int
    limit: int
    offset: int


class RunScreenerHandler:

    def __init__(self, financial_repo: IFinancialRepo) -> None:
        self._repo = financial_repo

    async def handle(self, query: ScreenerQuery) -> ScreenerResult:
        items = await self._repo.screen(
            pe_max=query.pe_max,
            pe_min=query.pe_min,
            roe_min=query.roe_min,
            ev_ebitda_max=query.ev_ebitda_max,
            debt_equity_max=query.debt_equity_max,
            sector=query.sector,
            limit=query.limit,
            offset=query.offset,
        )
        return ScreenerResult(
            items=items,
            total=len(items),
            limit=query.limit,
            offset=query.offset,
        )
