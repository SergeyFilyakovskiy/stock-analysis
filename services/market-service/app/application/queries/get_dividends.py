from dataclasses import dataclass
from typing import Optional

from app.application.dto import DividendDto
from app.domain.entities import Dividend
from app.domain.exceptions import TickerNotFoundError
from app.domain.interfaces import IMarketRepository


@dataclass(frozen=True)
class GetDividendsQuery:
    ticker:    str
    from_date: Optional[str] = None
    to_date:   Optional[str] = None


def _to_dto(d: Dividend) -> DividendDto:
    return DividendDto(
        ticker=d.ticker,
        ex_date=d.ex_date,
        pay_date=d.pay_date,
        amount=d.amount,
        currency=d.currency,
    )


class GetDividendsHandler:

    def __init__(self, repo: IMarketRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetDividendsQuery) -> list[DividendDto]:
        ticker = query.ticker.upper()

        security = await self._repo.get_security(ticker)
        if not security:
            raise TickerNotFoundError(ticker)

        dividends = await self._repo.get_dividends(
            ticker=ticker,
            from_date=query.from_date,
            to_date=query.to_date,
        )
        return [_to_dto(d) for d in dividends]