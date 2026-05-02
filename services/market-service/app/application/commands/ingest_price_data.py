from dataclasses import dataclass
from datetime import datetime

from app.domain.interfaces import IMarketRepository
from app.infrastructure.external.facade import MarketDataFacade
from app.infrastructure.messaging.publisher import MarketEventPublisher


@dataclass(frozen=True)
class IngestPriceDataCommand:
    ticker:   str
    from_dt:  datetime
    to_dt:    datetime
    interval: str = "1m"


class IngestPriceDataHandler:

    def __init__(
        self,
        repo:      IMarketRepository,
        facade:    MarketDataFacade,
        publisher: MarketEventPublisher,
    ) -> None:
        self._repo      = repo
        self._facade    = facade
        self._publisher = publisher

    async def handle(self, command: IngestPriceDataCommand) -> None:
        ticker = command.ticker.upper()

        bars = await self._facade.get_historical_bars(
            ticker=ticker,
            from_dt=command.from_dt,
            to_dt=command.to_dt,
            interval=command.interval,
        )

        if not bars:
            return

        await self._repo.save_price_bars(bars)

        # Публикуем событие о последней цене
        last_bar = bars[-1]
        await self._publisher.publish_price_updated(
            ticker=ticker,
            price=last_bar.close,
            timestamp=last_bar.time,
        )