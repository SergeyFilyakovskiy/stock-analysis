from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CompanySchema(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    market_cap: Optional[Decimal] = None
    country: str


class FinancialMetricsSchema(BaseModel):
    ticker: str
    calculated_at: date
    pe: Optional[Decimal] = None
    pb: Optional[Decimal] = None
    ps: Optional[Decimal] = None
    ev_ebitda: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    roa: Optional[Decimal] = None
    roic: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    net_margin: Optional[Decimal] = None
    ebitda_margin: Optional[Decimal] = None
    debt_equity: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None

    @field_serializer(
        "pe", "pb", "ps", "ev_ebitda", "roe", "roa", "roic",
        "gross_margin", "net_margin", "ebitda_margin",
        "debt_equity", "dividend_yield",
        when_used="json",
    )
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[float]:
        return float(v) if v is not None else None


class ValuationSchema(BaseModel):
    model_name: str
    estimated_value: Decimal
    current_price: Decimal
    confidence_score: float
    is_undervalued: bool
    upside_pct: Decimal


class FinancialReportSchema(BaseModel):
    period: str
    period_type: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    revenue: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None
    eps_diluted: Optional[Decimal] = None
    source: str


class AnalystRatingSchema(BaseModel):
    analyst_firm: str
    rating: str
    target_price: Optional[Decimal] = None
    rating_date: date


class CompanyReportSchema(BaseModel):
    ticker: str
    company: Optional[CompanySchema] = None
    current_price: Decimal = Decimal("0")
    metrics: Optional[FinancialMetricsSchema] = None
    reports: list[FinancialReportSchema] = []
    valuations: list[ValuationSchema] = []
    analyst_ratings: list[AnalystRatingSchema] = []


class ScreenerFilterSchema(BaseModel):
    pe_max: Optional[float] = Field(None, ge=0)
    pe_min: Optional[float] = Field(None, ge=0)
    roe_min: Optional[float] = None
    ev_ebitda_max: Optional[float] = Field(None, ge=0)
    debt_equity_max: Optional[float] = Field(None, ge=0)
    sector: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class ScreenerResultSchema(BaseModel):
    items: list[FinancialMetricsSchema]
    total: int
    limit: int
    offset: int


class CompareRequestSchema(BaseModel):
    tickers: list[str] = Field(..., min_length=2, max_length=10)
    include_valuation: bool = True
