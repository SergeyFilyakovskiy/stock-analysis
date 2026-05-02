from datetime import datetime
from decimal import Decimal

import httpx

from app.domain.entities import PriceBar
from app.domain.exceptions import ProviderUnavailableError
from app.infrastructure.external.base import BaseMarketDataProvider


class AlphaVantageProvider(BaseMarketDataProvider):

    BASE_URL = "https://www.alphavantage.co/query"

    # Маппинг наших интервалов → интервалы Alpha Vantage
    _INTERVAL_MAP = {
        "1m":  "1min",
        "5m":  "5min",
        "15m": "15min",
        "30m": "30min",
        "1h":  "60min",
    }

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client  = httpx.AsyncClient(timeout=10.0)

    @property
    def name(self) -> str:
        return "alphavantage"

    async def get_last_price(self, ticker: str) -> Decimal:
        try:
            response = await self._client.get(self.BASE_URL, params={
                "function":   "GLOBAL_QUOTE",
                "symbol":     ticker.upper(),
                "apikey":     self._api_key,
            })
            response.raise_for_status()
            data = response.json()
            price = data["Global Quote"]["05. price"]
            return Decimal(price)
        except Exception as e:
            raise ProviderUnavailableError(self.name) from e

    async def get_historical_bars(
        self,
        ticker: str,
        from_dt: datetime,
        to_dt: datetime,
        interval: str,
    ) -> list[PriceBar]:
        av_interval = self._INTERVAL_MAP.get(interval)

        # Alpha Vantage не поддерживает 4h и 1d через intraday
        if not av_interval:
            raise ProviderUnavailableError(self.name)

        try:
            response = await self._client.get(self.BASE_URL, params={
                "function":         "TIME_SERIES_INTRADAY",
                "symbol":           ticker.upper(),
                "interval":         av_interval,
                "outputsize":       "full",
                "apikey":           self._api_key,
            })
            response.raise_for_status()
            data     = response.json()
            key      = f"Time Series ({av_interval})"
            ts_data  = data.get(key, {})

            bars = []
            for ts_str, values in ts_data.items():
                bar_time = datetime.fromisoformat(ts_str)
                if from_dt <= bar_time <= to_dt:
                    bars.append(PriceBar(
                        time=bar_time,
                        ticker=ticker.upper(),
                        open=Decimal(values["1. open"]),
                        high=Decimal(values["2. high"]),
                        low=Decimal(values["3. low"]),
                        close=Decimal(values["4. close"]),
                        volume=int(values["5. volume"]),
                        source=self.name,
                    ))

            return sorted(bars, key=lambda b: b.time)

        except ProviderUnavailableError:
            raise
        except Exception as e:
            raise ProviderUnavailableError(self.name) from e