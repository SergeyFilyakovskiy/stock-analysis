from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Company:
    ticker: str
    name: str
    sector: str
    industry: str
    market_cap: Optional[Decimal] = None
    country: str = "US"
    description: Optional[str] = None


@dataclass
class FinancialReport:
    ticker: str
    period: str          # "2024Q1", "2024FY"
    period_type: str     # "quarterly" | "annual"
    fiscal_year: int
    fiscal_quarter: Optional[int]  # None для annual

    revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    eps: Optional[Decimal] = None
    eps_diluted: Optional[Decimal] = None

    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    cash_and_equivalents: Optional[Decimal] = None

    operating_cash_flow: Optional[Decimal] = None
    capital_expenditures: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None

    report_date: Optional[date] = None
    source: str = "polygon"  # "polygon" | "alpha_vantage"


@dataclass
class FinancialMetrics:
    ticker: str
    calculated_at: date

    # Мультипликаторы оценки
    pe: Optional[Decimal] = None       # Price / EPS
    pb: Optional[Decimal] = None       # Price / Book Value
    ps: Optional[Decimal] = None       # Price / Sales
    ev_ebitda: Optional[Decimal] = None

    # Рентабельность
    roe: Optional[Decimal] = None      # Net Income / Equity
    roa: Optional[Decimal] = None      # Net Income / Assets
    roic: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    net_margin: Optional[Decimal] = None
    ebitda_margin: Optional[Decimal] = None

    # Долговая нагрузка
    debt_equity: Optional[Decimal] = None
    current_ratio: Optional[Decimal] = None
    interest_coverage: Optional[Decimal] = None

    # Денежный поток
    fcf_yield: Optional[Decimal] = None
    fcf_per_share: Optional[Decimal] = None

    # Дивиденды
    dividend_yield: Optional[Decimal] = None
    payout_ratio: Optional[Decimal] = None


@dataclass
class TechnicalSignal:
    ticker: str
    signal_type: str     # "RSI", "MACD", "BB", ...
    value: Decimal
    signal: str          # "buy" | "sell" | "neutral"
    timestamp: date
    timeframe: str = "1D"
    metadata: dict = field(default_factory=dict)


@dataclass
class AnalystRating:
    ticker: str
    analyst_firm: str
    rating: str          # "buy" | "hold" | "sell" | "strong_buy" | "strong_sell"
    target_price: Optional[Decimal]
    rating_date: date
    previous_rating: Optional[str] = None
    previous_target: Optional[Decimal] = None