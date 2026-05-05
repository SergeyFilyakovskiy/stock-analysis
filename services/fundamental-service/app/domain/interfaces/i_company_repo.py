from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import Company


class ICompanyRepo(ABC):

    @abstractmethod
    async def get_by_ticker(self, ticker: str) -> Optional[Company]:
        ...

    @abstractmethod
    async def save(self, company: Company) -> None:
        ...

    @abstractmethod
    async def exists(self, ticker: str) -> bool:
        ...

    @abstractmethod
    async def get_all_tickers(self) -> list[str]:
        ...