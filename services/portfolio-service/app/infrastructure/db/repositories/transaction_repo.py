from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Transaction
from app.domain.interfaces.i_transaction_repo import ITransactionRepo
from app.domain.value_objects import Money, Quantity, Ticker
from app.infrastructure.db.models import TransactionModel


class TransactionRepo(ITransactionRepo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transaction: Transaction) -> None:
        self._session.add(
            TransactionModel(
                id=transaction.id,
                portfolio_id=transaction.portfolio_id,
                ticker=str(transaction.ticker),
                transaction_type=transaction.transaction_type,
                price=transaction.price.amount,
                quantity=transaction.quantity.value,
                currency=transaction.price.currency,
                created_at=transaction.created_at,
            )
        )

    async def get_by_portfolio(
        self,
        portfolio_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        result = await self._session.execute(
            select(TransactionModel)
            .where(TransactionModel.portfolio_id == portfolio_id)
            .order_by(TransactionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    @staticmethod
    def _to_entity(row: TransactionModel) -> Transaction:
        return Transaction(
            id=row.id,
            portfolio_id=row.portfolio_id,
            ticker=Ticker(row.ticker),
            transaction_type=row.transaction_type,
            price=Money(row.price, row.currency),
            quantity=Quantity(row.quantity),
            created_at=row.created_at,
        )