from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.domain.entities import FinancialReport
from app.domain.exceptions import ExternalAPIError
from app.infrastructure.external.base import BaseFinancialProvider


class PolygonProvider(BaseFinancialProvider):
    """
    Клиент Polygon.io.
    Endpoint: GET /vX/reference/financials
    Docs: https://polygon.io/docs/stocks/get_vx_reference_financials
    """

    @property
    def provider_name(self) -> str:
        return "polygon"

    async def get_financials(
        self,
        ticker: str,
        limit: int = 8,
        period_type: str = "annual",
    ) -> list[FinancialReport]:
        timeframe = "annual" if period_type == "annual" else "quarterly"
        url = f"{settings.POLYGON_BASE_URL}/vX/reference/financials"
        params = {
            "ticker": ticker,
            "timeframe": timeframe,
            "limit": limit,
            "apiKey": settings.POLYGON_KEY,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                raise ExternalAPIError(
                    "polygon",
                    f"GET /vX/reference/financials → {resp.status_code}: {resp.text[:200]}",
                )
            data = resp.json()

        results = data.get("results", [])
        return [self._parse_report(ticker, r, period_type) for r in results]

    async def get_company_details(self, ticker: str) -> dict:
        url = f"{settings.POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
        params = {"apiKey": settings.POLYGON_KEY.get_secret_value()}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                raise ExternalAPIError(
                    "polygon",
                    f"GET /v3/reference/tickers/{ticker} → {resp.status_code}",
                )
            return resp.json().get("results", {})

    @staticmethod
    def _parse_report(
        ticker: str, data: dict[str, Any], period_type: str
    ) -> FinancialReport:
        ic = data.get("financials", {}).get("income_statement", {})
        bs = data.get("financials", {}).get("balance_sheet", {})
        cf = data.get("financials", {}).get("cash_flow_statement", {})

        def dec(d: dict, key: str) -> Decimal | None:
            v = d.get(key, {}).get("value")
            return Decimal(str(v)) if v is not None else None

        fiscal_period: str = data.get("fiscal_period", "FY")   # Q1/Q2/Q3/Q4/FY
        fiscal_year: int = int(data.get("fiscal_year", 0))

        if fiscal_period == "FY":
            period_str = f"{fiscal_year}FY"
            quarter = None
        else:
            q = int(fiscal_period[1])
            period_str = f"{fiscal_year}Q{q}"
            quarter = q

        report_date_raw = data.get("filing_date") or data.get("end_date")
        try:
            report_date = date.fromisoformat(report_date_raw) if report_date_raw else None
        except ValueError:
            report_date = None

        revenues = dec(ic, "revenues")
        net_income_loss = dec(ic, "net_income_loss")
        ebitda = dec(ic, "ebitda")
        eps = dec(ic, "basic_earnings_per_share")
        eps_diluted = dec(ic, "diluted_earnings_per_share")

        total_assets = dec(bs, "assets")
        total_liabilities = dec(bs, "liabilities")
        total_equity = dec(bs, "equity")
        total_debt = dec(bs, "long_term_debt")
        cash = dec(bs, "cash_and_cash_equivalents_including_short_term_investments")

        ocf = dec(cf, "net_cash_flow_from_operating_activities")
        capex = dec(cf, "capital_expenditure")
        fcf = (ocf + capex) if ocf and capex else None  # capex обычно отрицательный

        return FinancialReport(
            ticker=ticker,
            period=period_str,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=quarter,
            revenue=revenues,
            net_income=net_income_loss,
            ebitda=ebitda,
            eps=eps,
            eps_diluted=eps_diluted,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            total_debt=total_debt,
            cash_and_equivalents=cash,
            operating_cash_flow=ocf,
            capital_expenditures=capex,
            free_cash_flow=fcf,
            report_date=report_date,
            source="polygon",
        )
