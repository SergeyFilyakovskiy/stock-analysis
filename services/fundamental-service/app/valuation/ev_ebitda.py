from decimal import Decimal

from app.domain.entities import FinancialReport, FinancialMetrics
from app.domain.exceptions import InsufficientDataError
from app.domain.interfaces.i_valuation_model import IValuationModel
from app.domain.value_objects import ValuationResult


class EVEBITDAModel(IValuationModel):
    """
    EV/EBITDA Relative Valuation.

    Формула:
        Enterprise Value = EBITDA_ttm * Target_Multiple
        Equity Value     = EV - Net Debt
        Fair Price       = Equity Value / Shares Outstanding

    Target multiple: sector average или исторический EV/EBITDA компании.
    """

    def __init__(self, target_multiple: float | None = None) -> None:
        self._target_multiple = (
            Decimal(str(target_multiple)) if target_multiple else None
        )

    @property
    def model_name(self) -> str:
        return "EV_EBITDA"

    def confidence_score(
        self,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
    ) -> float:
        score = 0.0
        ttm_ebitda = self._get_ttm_ebitda(reports)
        if ttm_ebitda and ttm_ebitda > 0:
            score += 0.4
        if metrics.ev_ebitda and metrics.ev_ebitda > 0:
            score += 0.3
        if self._target_multiple is not None:
            score += 0.2
        # Наличие долговых данных для расчёта net debt
        latest = self._latest_annual(reports)
        if latest and latest.total_debt is not None and latest.cash_and_equivalents is not None:
            score += 0.1
        return round(score, 2)

    async def estimate(
        self,
        ticker: str,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
        current_price: Decimal,
    ) -> ValuationResult:
        ttm_ebitda = self._get_ttm_ebitda(reports)
        if not ttm_ebitda or ttm_ebitda <= 0:
            raise InsufficientDataError("EV_EBITDA", ["ebitda (TTM > 0)"])

        multiple = self._target_multiple or metrics.ev_ebitda
        if not multiple or multiple <= 0:
            raise InsufficientDataError("EV_EBITDA", ["target_multiple or ev_ebitda"])

        ev = ttm_ebitda * multiple

        # Вычитаем net debt
        latest = self._latest_annual(reports)
        net_debt = Decimal("0")
        if latest:
            debt = latest.total_debt or Decimal("0")
            cash = latest.cash_and_equivalents or Decimal("0")
            net_debt = debt - cash

        equity_value = ev - net_debt

        # Shares outstanding через EPS
        per_share = current_price  # fallback
        if latest and latest.eps and latest.eps > 0 and latest.net_income:
            shares = latest.net_income / latest.eps
            if shares > 0:
                per_share = (equity_value / shares).quantize(Decimal("0.01"))

        confidence = self.confidence_score(reports, metrics)

        return ValuationResult(
            ticker=ticker,
            model_name=self.model_name,
            estimated_value=per_share,
            current_price=current_price,
            confidence_score=confidence,
        )

    @staticmethod
    def _get_ttm_ebitda(reports: list[FinancialReport]) -> Decimal | None:
        quarterly = sorted(
            [r for r in reports if r.period_type == "quarterly" and r.ebitda],
            key=lambda r: (r.fiscal_year, r.fiscal_quarter or 0),
            reverse=True,
        )
        if len(quarterly) >= 4:
            return sum(r.ebitda for r in quarterly[:4])
        annual = [r for r in reports if r.period_type == "annual" and r.ebitda]
        if annual:
            return max(annual, key=lambda r: r.fiscal_year).ebitda
        return None

    @staticmethod
    def _latest_annual(reports: list[FinancialReport]) -> FinancialReport | None:
        annual = [r for r in reports if r.period_type == "annual"]
        return max(annual, key=lambda r: r.fiscal_year) if annual else None