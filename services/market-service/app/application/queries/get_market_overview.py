from dataclasses import dataclass

from app.application.dto import MarketIndexDto
from app.domain.entities import MarketIndex
from app.domain.interfaces import IMarketRepository


@dataclass(frozen=True)
class GetMarketOverviewQuery:
    pass


def _to_dto(m: MarketIndex) -> MarketIndexDto:
    return MarketIndexDto(
        index_code=m.index_code,
        name=m.name,
        description=m.description,
        is_active=m.is_active,
    )


class GetMarketOverviewHandler:

    def __init__(self, repo: IMarketRepository) -> None:
        self._repo = repo

    async def handle(self, query: GetMarketOverviewQuery) -> list[MarketIndexDto]:
        indices = await self._repo.get_market_indices()
        return [_to_dto(i) for i in indices]