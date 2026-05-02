from dataclasses import dataclass

from app.application.dto import SecurityDto
from app.domain.entities import Security
from app.domain.interfaces import IMarketRepository


@dataclass(frozen=True)
class SearchSecuritiesQuery:
    query: str


def _to_dto(s: Security) -> SecurityDto:
    return SecurityDto(
        ticker=s.ticker,
        name=s.name,
        exchange=s.exchange,
        sector=s.sector,
        is_active=s.is_active,
    )


class SearchSecuritiesHandler:

    def __init__(self, repo: IMarketRepository) -> None:
        self._repo = repo

    async def handle(self, query: SearchSecuritiesQuery) -> list[SecurityDto]:
        securities = await self._repo.search_securities(query.query)
        return [_to_dto(s) for s in securities]