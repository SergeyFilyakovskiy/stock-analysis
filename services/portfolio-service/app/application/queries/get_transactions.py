from dataclasses import dataclass
from uuid import UUID

from app.application.dto import TransactionDTO
from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.infrastructure.db.repositories.transaction_repo import TransactionRepo
from app.infrastructure.db.repositories.portfolio_repo import PortfolioRepo


@dataclass
class GetTransactionsQuery:
    portfolio_id: UUID
    user_id: UUID
    limit: int = 50
    offset: int = 0


class GetTransactionsHandler:
    def __init__(self, portfolio_repo: PortfolioRepo, transaction_repo: TransactionRepo) -> None:
        self._portfolios = portfolio_repo
        self._transactions = transaction_repo

    async def handle(self, query: GetTransactionsQuery) -> list[TransactionDTO]:
        portfolio = await self._portfolios.get_by_id(query.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(query.portfolio_id))
        if portfolio.user_id != query.user_id:
            raise PortfolioAccessDenied(str(query.portfolio_id))

        txs = await self._transactions.get_by_portfolio(
            query.portfolio_id, limit=query.limit, offset=query.offset
        )
        return [
            TransactionDTO(
                id=tx.id,
                ticker=str(tx.ticker),
                transaction_type=tx.transaction_type,
                price=tx.price.amount,
                quantity=tx.quantity.value,
                currency=tx.price.currency,
                created_at=tx.created_at,
            )
            for tx in txs
        ]