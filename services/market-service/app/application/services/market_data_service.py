from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.application.commands.ingest_price_data import (
    IngestPriceDataCommand,
    IngestPriceDataHandler,
)
from app.application.dto import DividendDto, OHLCVDto, SecurityDto, MarketIndexDto
from app.application.queries.get_dividends import GetDividendsHandler, GetDividendsQuery
from app.application.queries.get_last_price import GetLastPriceHandler, GetLastPriceQuery
from app.application.queries.get_market_overview import GetMarketOverviewHandler, GetMarketOverviewQuery
from app.application.queries.get_ohlcv import GetOHLCVHandler, GetOHLCVQuery
from app.application.queries.search_securities import SearchSecuritiesHandler, SearchSecuritiesQuery


class MarketDataService:
    """
    Фасад application-слоя.
    Эндпоинты и воркеры работают только через него.
    """

    def __init__(
        self,
        get_last_price_handler:    GetLastPriceHandler,
        get_ohlcv_handler:         GetOHLCVHandler,
        search_securities_handler: SearchSecuritiesHandler,
        get_market_overview_handler: GetMarketOverviewHandler,
        get_dividends_handler:     GetDividendsHandler,
        ingest_handler:            IngestPriceDataHandler,
    ) -> None:
        self._get_last_price      = get_last_price_handler
        self._get_ohlcv           = get_ohlcv_handler
        self._search_securities   = search_securities_handler
        self._get_market_overview = get_market_overview_handler
        self._get_dividends       = get_dividends_handler
        self._ingest              = ingest_handler

    async def get_last_price(self, ticker: str) -> Decimal:
        return await self._get_last_price.handle(GetLastPriceQuery(ticker=ticker))

    async def get_ohlcv(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> OHLCVDto:
        return await self._get_ohlcv.handle(
            GetOHLCVQuery(ticker=ticker, from_dt=from_dt, to_dt=to_dt, interval=interval)
        )

    async def search_securities(self, query: str) -> list[SecurityDto]:
        return await self._search_securities.handle(SearchSecuritiesQuery(query=query))

    async def get_market_overview(self) -> list[MarketIndexDto]:
        return await self._get_market_overview.handle(GetMarketOverviewQuery())

    async def get_dividends(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[DividendDto]:
        return await self._get_dividends.handle(
            GetDividendsQuery(ticker=ticker, from_date=from_date, to_date=to_date)
        )

    async def ingest_price_data(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str = "1m",
    ) -> None:
        await self._ingest.handle(
            IngestPriceDataCommand(
                ticker=ticker,
                from_dt=from_dt,
                to_dt=to_dt,
                interval=interval,
            )
        )