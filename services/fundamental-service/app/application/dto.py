from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from app.domain.entities import AnalystRating, Company, FinancialMetrics, FinancialReport
from app.domain.value_objects import ValuationResult


@dataclass
class CompanyReportDTO:
    """DTO для передачи между application и api слоями."""
    ticker: str
    company: Optional[Company] = None
    metrics: Optional[FinancialMetrics] = None
    reports: list[FinancialReport] = field(default_factory=list)
    valuations: list[ValuationResult] = field(default_factory=list)
    analyst_ratings: list[AnalystRating] = field(default_factory=list)
    current_price: Decimal = Decimal("0")
