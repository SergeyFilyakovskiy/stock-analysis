from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.domain.entities import FinancialReport
from app.domain.exceptions import ExternalAPIError
from app.infrastructure.external.base import BaseFinancialProvider


class AlphaVantageProvider(BaseFinancialProvider):
    """
    Fallback-провайдер через Alpha Vantage.
    Используется если Polygon не вернул данные.
    """

    @property
    def provider_name(self) -> str:
        return "alpha_vantage"

    async def get_financials(
        self,
        ticker: str,
        limit: int = 8,
        period_type: str = "annual",
    ) -> list[FinancialReport]:
        function = "INCOME_STATEMENT"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{settings.ALPHA_VANTAGE_BASE_URL}/query",
                params={
                    "function": function,
                    "symbol": ticker,
                    "apikey": settings.ALPHA_VANTAGE_KEY.get_secret_value(),
                },
            )
            if resp.status_code != 200:
                raise ExternalAPIError("alpha_vantage", f"{resp.status_code}: {resp.text[:200]}")
            data = resp.json()

        key = "annualReports" if period_type == "annual" else "quarterlyReports"
        reports_raw = data.get(key, [])[:limit]
        return [
            self._parse_report(ticker, r, period_type, i)
            for i, r in enumerate(reports_raw)
        ]

    async def get_company_details(self, ticker: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.ALPHA_VANTAGE_BASE_URL}/query",
                params={
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": settings.ALPHA_VANTAGE_KEY.get_secret_value(),
                },
            )
            if resp.status_code != 200:
                raise ExternalAPIError("alpha_vantage", f"{resp.status_code}")
            return resp.json()

    @staticmethod
    def _parse_report(
        ticker: str, data: dict[str, Any], period_type: str, index: int
    ) -> FinancialReport:
        def dec(key: str) -> Decimal | None:
            v = data.get(key)
            if v in (None, "None", ""):
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return None

        fiscal_date = data.get("fiscalDateEnding", "")
        year = int(fiscal_date[:4]) if fiscal_date else 2024
        period_str = f"{year}FY" if period_type == "annual" else f"{year}Q{4 - index % 4}"
        quarter = None if period_type == "annual" else (4 - index % 4)

        net_income = dec("netIncome")
        ocf = dec("operatingCashflow")
        capex = dec("capitalExpenditures")
        fcf = (ocf - capex) if ocf and capex else None

        return FinancialReport(
            ticker=ticker,
            period=period_str,
            period_type=period_type,
            fiscal_year=year,
            fiscal_quarter=quarter,
            revenue=dec("totalRevenue"),
            gross_profit=dec("grossProfit"),
            operating_income=dec("operatingIncome"),
            net_income=net_income,
            ebitda=dec("ebitda"),
            eps=dec("reportedEPS"),
            total_assets=dec("totalAssets") if "totalAssets" in data else None,
            operating_cash_flow=ocf,
            capital_expenditures=capex,
            free_cash_flow=fcf,
            source="alpha_vantage",
        )
