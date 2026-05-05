from decimal import Decimal
from typing import Optional

from app.domain.entities import FinancialReport, FinancialMetrics
from app.domain.exceptions import InsufficientDataError
from app.domain.interfaces.i_valuation_model import IValuationModel
from app.domain.value_objects import ValuationResult


class DCFModel(IValuationModel):
    """
    Discounted Cash Flow.

    Формула:
        Intrinsic Value = sum(FCF_t / (1+r)^t) + Terminal Value / (1+r)^n
        Terminal Value  = FCF_n * (1 + g) / (r - g)

    Параметры по умолчанию консервативные:
        r = 10% (WACC),  g = 3% (terminal growth),  n = 5 лет прогноза
    """

    def __init__(
        self,
        wacc: float = 0.10,
        terminal_growth: float = 0.03,
        projection_years: int = 5,
        fcf_growth_rate: Optional[float] = None,  # если None — из исторических данных
    ) -> None:
        self._wacc = Decimal(str(wacc))
        self._g = Decimal(str(terminal_growth))
        self._n = projection_years
        self._fcf_growth_override = (
            Decimal(str(fcf_growth_rate)) if fcf_growth_rate else None
        )

    @property
    def model_name(self) -> str:
        return "DCF"

    def confidence_score(
        self,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
    ) -> float:
        score = 0.0
        annual = [r for r in reports if r.period_type == "annual"]
        # Чем больше годовых отчётов с FCF — тем выше уверенность
        fcf_count = sum(1 for r in annual if r.free_cash_flow is not None)
        score += min(fcf_count / 5, 1.0) * 0.6   # до 60% за 5 лет FCF
        if metrics.roic is not None:
            score += 0.2
        if metrics.debt_equity is not None:
            score += 0.2
        return round(score, 2)

    async def estimate(
        self,
        ticker: str,
        reports: list[FinancialReport],
        metrics: FinancialMetrics,
        current_price: Decimal,
    ) -> ValuationResult:
        annual = sorted(
            [r for r in reports if r.period_type == "annual" and r.free_cash_flow],
            key=lambda r: r.fiscal_year,
        )
        if not annual:
            raise InsufficientDataError("DCF", ["free_cash_flow (annual)"])

        last_fcf = annual[-1].free_cash_flow

        # Историческая средняя скорость роста FCF
        if self._fcf_growth_override is not None:
            growth = self._fcf_growth_override
        elif len(annual) >= 2:
            first_fcf = annual[0].free_cash_flow
            years = annual[-1].fiscal_year - annual[0].fiscal_year
            if first_fcf and first_fcf > 0 and years > 0:
                growth = (last_fcf / first_fcf) ** (Decimal(1) / years) - Decimal(1)
                growth = min(growth, Decimal("0.25"))  # cap 25%
            else:
                growth = Decimal("0.05")
        else:
            growth = Decimal("0.05")

        # Дисконтирование прогнозного FCF
        intrinsic = Decimal("0")
        fcf = last_fcf
        for t in range(1, self._n + 1):
            fcf = fcf * (1 + growth)
            intrinsic += fcf / (1 + self._wacc) ** t

        # Терминальная стоимость
        terminal_fcf = fcf * (1 + self._g)
        terminal_value = terminal_fcf / (self._wacc - self._g)
        intrinsic += terminal_value / (1 + self._wacc) ** self._n

        # Нужно поделить на количество акций — приближаем через market_cap / price
        # В реальном проекте shares_outstanding берётся из отчёта
        shares_outstanding = None
        for r in reversed(annual):
            if r.net_income and metrics.pe and metrics.pe > 0:
                # EPS * PE = price, EPS = net_income / shares
                # shares ≈ net_income / (price / PE)  — обходной путь
                if r.eps and r.eps > 0:
                    shares_outstanding = r.net_income / r.eps
                    break

        if shares_outstanding and shares_outstanding > 0:
            per_share = intrinsic / shares_outstanding
        else:
            # fallback: нормализуем через соотношение к рыночной цене
            per_share = intrinsic * current_price / (intrinsic + current_price)

        confidence = self.confidence_score(reports, metrics)

        return ValuationResult(
            ticker=ticker,
            model_name=self.model_name,
            estimated_value=per_share.quantize(Decimal("0.01")),
            current_price=current_price,
            confidence_score=confidence,
        )