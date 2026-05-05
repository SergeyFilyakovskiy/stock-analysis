import logging

from app.domain.entities import FinancialReport
from app.domain.exceptions import ExternalAPIError
from app.infrastructure.external.alpha_vantage import AlphaVantageProvider
from app.infrastructure.external.polygon import PolygonProvider

logger = logging.getLogger(__name__)


class FinancialDataFacade:
    """
    Facade: сначала пробует Polygon, при ошибке — fallback на Alpha Vantage.
    Вызывающий код не знает, какой провайдер ответил.
    """

    def __init__(self) -> None:
        self._polygon = PolygonProvider()
        self._alpha_vantage = AlphaVantageProvider()

    async def get_financials(
        self,
        ticker: str,
        limit: int = 8,
        period_type: str = "annual",
    ) -> list[FinancialReport]:
        try:
            reports = await self._polygon.get_financials(ticker, limit, period_type)
            if reports:
                return reports
            logger.warning("[Polygon] Empty response for %s, trying Alpha Vantage", ticker)
        except ExternalAPIError as e:
            logger.warning("[Polygon] Failed for %s: %s — trying Alpha Vantage", ticker, e)

        return await self._alpha_vantage.get_financials(ticker, limit, period_type)

    async def get_company_details(self, ticker: str) -> dict:
        try:
            details = await self._polygon.get_company_details(ticker)
            if details:
                return details
        except ExternalAPIError as e:
            logger.warning("[Polygon] get_company_details failed: %s", e)
        return await self._alpha_vantage.get_company_details(ticker)
