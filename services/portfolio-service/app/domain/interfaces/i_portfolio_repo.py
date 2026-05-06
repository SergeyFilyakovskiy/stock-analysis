from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Portfolio


class IPortfolioRepo(ABC):

    @abstractmethod
    async def get_by_id(self, portfolio_id: UUID) -> Portfolio | None: ...

    @abstractmethod
    async def get_all_by_user(self, user_id: UUID) -> list[Portfolio]: ...

    @abstractmethod
    async def save(self, portfolio: Portfolio) -> None: ...

    @abstractmethod
    async def delete(self, portfolio_id: UUID) -> None: ...