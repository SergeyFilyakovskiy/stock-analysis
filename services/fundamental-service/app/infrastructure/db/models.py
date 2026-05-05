from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Date, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    country: Mapped[str] = mapped_column(String(3), default="US", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reports: Mapped[list["FinancialReportModel"]] = relationship(
        back_populates="company", lazy="noload"
    )
    metrics: Mapped[Optional["FinancialMetricsModel"]] = relationship(
        back_populates="company", uselist=False, lazy="noload"
    )


class FinancialReportModel(Base):
    __tablename__ = "financial_reports"
    __table_args__ = (
        UniqueConstraint("ticker", "period", name="uq_report_ticker_period"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.ticker", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    period: Mapped[str] = mapped_column(String(10), nullable=False)       # "2024Q1"
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "quarterly"|"annual"
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # P&L
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    eps_diluted: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # Balance sheet
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Cash flow
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    capital_expenditures: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    report_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="polygon", nullable=False)

    company: Mapped["CompanyModel"] = relationship(back_populates="reports", lazy="noload")


class FinancialMetricsModel(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(10), ForeignKey("companies.ticker", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )
    calculated_at: Mapped[date] = mapped_column(Date, nullable=False)

    pe: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    pb: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    ps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    ev_ebitda: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    roe: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    roa: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    roic: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    gross_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    net_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    ebitda_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    debt_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    current_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    interest_coverage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    fcf_yield: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    fcf_per_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    dividend_yield: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    payout_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    company: Mapped["CompanyModel"] = relationship(back_populates="metrics", lazy="noload")


class TechnicalSignalModel(Base):
    """TimescaleDB hypertable — партиционируется по timestamp."""
    __tablename__ = "technical_signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    signal: Mapped[str] = mapped_column(String(10), nullable=False)  # buy|sell|neutral
    timestamp: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(5), default="1D", nullable=False)
    extra_data: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

class AnalystRatingModel(Base):
    __tablename__ = "analyst_ratings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    analyst_firm: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)
    target_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    rating_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    previous_rating: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    previous_target: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
