from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Transaction


class ITransactionRepo(ABC):

    @abstractmethod
    async def save(self, transaction: Transaction) -> None: ...

    @abstractmethod
    async def get_by_portfolio(
        self,
        portfolio_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]: ...