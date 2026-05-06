from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import PriceAlert


class IAlertRepo(ABC):

    @abstractmethod
    async def save(self, alert: PriceAlert) -> None: ...

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[PriceAlert]: ...

    @abstractmethod
    async def get_active_by_ticker(self, ticker: str) -> list[PriceAlert]: ...

    @abstractmethod
    async def delete(self, alert_id: UUID) -> None: ...

    @abstractmethod
    async def deactivate(self, alert_id: UUID) -> None: ...