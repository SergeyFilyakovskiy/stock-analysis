from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import AnalyticsPositionDTO, PortfolioAnalyticsDTO
from app.domain.exceptions import PortfolioNotFound, PortfolioAccessDenied
from app.infrastructure.cache.pnl_cache import PnlCache
from app.infrastructure.db.models import PortfolioModel, PositionModel


@dataclass
class GetPortfolioAnalyticsQuery:
    portfolio_id: UUID
    user_id: UUID


class GetPortfolioAnalyticsHandler:
    def __init__(self, session: AsyncSession, pnl_cache: PnlCache) -> None:
        self._session = session
        self._pnl_cache = pnl_cache

    async def handle(self, query: GetPortfolioAnalyticsQuery) -> PortfolioAnalyticsDTO:
        # 1. Проверяем кэш
        cached = await self._pnl_cache.get(query.portfolio_id)
        if cached:
            return PortfolioAnalyticsDTO(**cached)

        # 2. Загружаем данные
        portfolio = await self._session.get(PortfolioModel, query.portfolio_id)
        if not portfolio:
            raise PortfolioNotFound(str(query.portfolio_id))
        if portfolio.user_id != query.user_id:
            raise PortfolioAccessDenied(str(query.portfolio_id))

        result = await self._session.execute(
            select(PositionModel).where(PositionModel.portfolio_id == query.portfolio_id)
        )
        positions = result.scalars().all()

        if not positions:
            empty = PortfolioAnalyticsDTO(
                portfolio_id=query.portfolio_id,
                currency=portfolio.currency,
                total_cost=Decimal("0"),
                total_market_value=Decimal("0"),
                total_unrealized_pnl=Decimal("0"),
                total_unrealized_pnl_pct=Decimal("0"),
                positions=[],
            )
            return empty

        # 3. Получаем актуальные цены из Redis (market-service db=1)
        tickers = [p.ticker for p in positions]
        prices = await self._pnl_cache.get_prices_batch(tickers)

        # 4. Считаем аналитику
        position_dtos = []
        total_cost = Decimal("0")
        total_market_value = Decimal("0")

        for p in positions:
            current_price = prices.get(p.ticker)
            cost = p.avg_price * p.quantity
            market_val = (current_price * p.quantity) if current_price else cost
            total_cost += cost
            total_market_value += market_val

        for p in positions:
            current_price = prices.get(p.ticker)
            cost = p.avg_price * p.quantity
            market_val = (current_price * p.quantity) if current_price else cost
            unrealized_pnl = market_val - cost
            weight = (market_val / total_market_value * 100) if total_market_value else Decimal("0")

            position_dtos.append(
                AnalyticsPositionDTO(
                    ticker=p.ticker,
                    quantity=p.quantity,
                    avg_price=p.avg_price,
                    current_price=current_price,
                    market_value=market_val,
                    unrealized_pnl=unrealized_pnl,
                    weight_pct=round(weight, 2),
                )
            )

        total_pnl = total_market_value - total_cost
        total_pnl_pct = (
            (total_pnl / total_cost * 100) if total_cost else Decimal("0")
        )

        dto = PortfolioAnalyticsDTO(
            portfolio_id=query.portfolio_id,
            currency=portfolio.currency,
            total_cost=total_cost,
            total_market_value=total_market_value,
            total_unrealized_pnl=total_pnl,
            total_unrealized_pnl_pct=round(total_pnl_pct, 2),
            positions=position_dtos,
        )

        # 5. Кэшируем результат (TTL=30s)
        await self._pnl_cache.set(query.portfolio_id, dto.__dict__)
        return dto