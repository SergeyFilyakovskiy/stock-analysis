from decimal import Decimal

from app.domain.entities import FinancialReport, FinancialMetrics
from app.domain.exceptions import InsufficientDataError
from app.domain.interfaces.i_valuation_model import IValuationModel
from app.domain.value_objects import ValuationResult


class PERelativeModel(IValuationModel):
    """
    P/E Relative Valuation.

    Формула:
        Fair Value = EPS_ttm * Sector_Average_PE

    Если sector_pe не передан — используем исторический median P/E компании.
    """

    def __init__(self, sector_pe: float | None = None) -> None:
        self._sector_pe = Decimal(str(sector_pe)) if sector_pe else None

    @property
    def model_name(self) -> str:
        return "PE_Relative"

    def confidence_score(
        self,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
    ) -> float:
        score = 0.0
        if metrics.pe is not None and metrics.pe > 0:
            score += 0.4
        ttm_eps = self._get_ttm_eps(reports)
        if ttm_eps is not None and ttm_eps > 0:
            score += 0.4
        if self._sector_pe is not None:
            score += 0.2  # внешний ориентир повышает надёжность
        return round(score, 2)

    async def estimate(
        self,
        ticker: str,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
        current_price: Decimal,
    ) -> ValuationResult:
        ttm_eps = self._get_ttm_eps(reports)
        if ttm_eps is None or ttm_eps <= 0:
            raise InsufficientDataError("PE_Relative", ["eps_diluted (TTM > 0)"])

        target_pe = self._sector_pe or metrics.pe
        if target_pe is None or target_pe <= 0:
            raise InsufficientDataError("PE_Relative", ["sector_pe or current pe"])

        fair_value = (ttm_eps * target_pe).quantize(Decimal("0.01"))
        confidence = self.confidence_score(reports, metrics)

        return ValuationResult(
            ticker=ticker,
            model_name=self.model_name,
            estimated_value=fair_value,
            current_price=current_price,
            confidence_score=confidence,
        )

    @staticmethod
    def _get_ttm_eps(reports: list[FinancialReport]) -> Decimal | None:
        """TTM EPS = сумма EPS за последние 4 квартала."""
        quarterly = sorted(
            [r for r in reports if r.period_type == "quarterly" and r.eps_diluted],
            key=lambda r: (r.fiscal_year, r.fiscal_quarter or 0),
            reverse=True,
        )
        if len(quarterly) >= 4:
            return sum(r.eps_diluted for r in quarterly[:4])
        # Fallback: последний годовой
        annual = [r for r in reports if r.period_type == "annual" and r.eps_diluted]
        if annual:
            return max(annual, key=lambda r: r.fiscal_year).eps_diluted
        return None
