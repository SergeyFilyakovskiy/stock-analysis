from datetime import datetime
from decimal import Decimal

import httpx

from app.domain.entities import PriceBar
from app.domain.exceptions import ProviderUnavailableError
from app.infrastructure.external.base import BaseMarketDataProvider


class PolygonProvider(BaseMarketDataProvider):

    BASE_URL = "https://api.polygon.io"

    _INTERVAL_MAP = {
        "1m":  ("minute", 1),
        "5m":  ("minute", 5),
        "15m": ("minute", 15),
        "30m": ("minute", 30),
        "1h":  ("hour",   1),
        "4h":  ("hour",   4),
        "1d":  ("day",    1),
    }

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client  = httpx.AsyncClient(
            timeout=10.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @property
    def name(self) -> str:
        return "polygon"

    async def get_last_price(self, ticker: str) -> Decimal:
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/v2/last/trade/{ticker.upper()}"
            )
            response.raise_for_status()
            data = response.json()
            return Decimal(str(data["results"]["p"]))
        except Exception as e:
            raise ProviderUnavailableError(self.name) from e

    async def get_historical_bars(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        timespan, multiplier = self._INTERVAL_MAP.get(interval, ("minute", 1))

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/v2/aggs/ticker/{ticker.upper()}/range"
                f"/{multiplier}/{timespan}"
                f"/{from_dt.strftime('%Y-%m-%d')}"
                f"/{to_dt.strftime('%Y-%m-%d')}",
                params={"adjusted": "true", "sort": "asc", "limit": 50000},
            )
            response.raise_for_status()
            data    = response.json()
            results = data.get("results", [])

            return [
                PriceBar(
                    time=datetime.fromtimestamp(r["t"] / 1000),
                    ticker=ticker.upper(),
                    open=Decimal(str(r["o"])),
                    high=Decimal(str(r["h"])),
                    low=Decimal(str(r["l"])),
                    close=Decimal(str(r["c"])),
                    volume=int(r["v"]),
                    source=self.name,
                )
                for r in results
            ]

        except ProviderUnavailableError:
            raise
        except Exception as e:
            raise ProviderUnavailableError(self.name) from e