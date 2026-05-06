from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Position


class IPositionRepo(ABC):

    @abstractmethod
    async def get_by_portfolio(self, portfolio_id: UUID) -> list[Position]: ...

    @abstractmethod
    async def save(self, position: Position) -> None: ...

    @abstractmethod
    async def delete_by_portfolio(self, portfolio_id: UUID) -> None: ...