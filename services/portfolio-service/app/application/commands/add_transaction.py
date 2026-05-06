from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.domain.value_objects import Money, Quantity, Ticker
from app.infrastructure.db.unit_of_work import UnitOfWork
from app.infrastructure.cache.pnl_cache import PnlCache


@dataclass
class AddTransactionCommand:
    portfolio_id: UUID
    user_id: UUID
    ticker: str
    transaction_type: str          # "BUY" | "SELL"
    price: Decimal
    quantity: Decimal
    currency: str = "USD"


class AddTransactionHandler:
    def __init__(self, uow: UnitOfWork, pnl_cache: PnlCache) -> None:
        self._uow = uow
        self._pnl_cache = pnl_cache

    async def handle(self, command: AddTransactionCommand) -> UUID:
        portfolio = await self._uow.portfolios.get_by_id(command.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(command.portfolio_id))
        if portfolio.user_id != command.user_id:
            raise PortfolioAccessDenied(str(command.portfolio_id))

        # Подгружаем позиции в агрегат
        positions = await self._uow.positions.get_by_portfolio(command.portfolio_id)
        portfolio.positions = positions

        ticker = Ticker(command.ticker)
        quantity = Quantity(command.quantity)
        price = Money(command.price, command.currency)
        tx_id = uuid4()

        if command.transaction_type == "BUY":
            tx = portfolio.apply_buy(ticker, quantity, price, tx_id)
        else:
            tx = portfolio.apply_sell(ticker, quantity, price, tx_id)

        # Сохраняем транзакцию и обновлённые позиции
        await self._uow.transactions.save(tx)
        for position in portfolio.positions:
            await self._uow.positions.save(position)

        events = portfolio.collect_events()
        await self._uow.commit_with_events(events)

        # Инвалидируем P&L кэш явно
        await self._pnl_cache.invalidate(command.portfolio_id)

        return tx_id