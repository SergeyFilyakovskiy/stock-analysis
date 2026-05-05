"""init analysis_db tables

Revision ID: 0001
Revises:
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # companies
    op.create_table(
        "companies",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("market_cap", sa.Numeric(20, 2), nullable=True),
        sa.Column("country", sa.String(3), server_default="US", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"])

    # financial_reports
    op.create_table(
        "financial_reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(10), sa.ForeignKey("companies.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("period_type", sa.String(10), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_quarter", sa.Integer(), nullable=True),
        sa.Column("revenue", sa.Numeric(20, 2), nullable=True),
        sa.Column("gross_profit", sa.Numeric(20, 2), nullable=True),
        sa.Column("operating_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("net_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("ebitda", sa.Numeric(20, 2), nullable=True),
        sa.Column("eps", sa.Numeric(10, 4), nullable=True),
        sa.Column("eps_diluted", sa.Numeric(10, 4), nullable=True),
        sa.Column("total_assets", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_liabilities", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_equity", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_debt", sa.Numeric(20, 2), nullable=True),
        sa.Column("cash_and_equivalents", sa.Numeric(20, 2), nullable=True),
        sa.Column("operating_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("capital_expenditures", sa.Numeric(20, 2), nullable=True),
        sa.Column("free_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(20), server_default="polygon", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "period", name="uq_report_ticker_period"),
    )
    op.create_index("ix_financial_reports_ticker", "financial_reports", ["ticker"])

    # financial_metrics
    op.create_table(
        "financial_metrics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(10), sa.ForeignKey("companies.ticker", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("calculated_at", sa.Date(), nullable=False),
        sa.Column("pe", sa.Numeric(10, 4), nullable=True),
        sa.Column("pb", sa.Numeric(10, 4), nullable=True),
        sa.Column("ps", sa.Numeric(10, 4), nullable=True),
        sa.Column("ev_ebitda", sa.Numeric(10, 4), nullable=True),
        sa.Column("roe", sa.Numeric(10, 4), nullable=True),
        sa.Column("roa", sa.Numeric(10, 4), nullable=True),
        sa.Column("roic", sa.Numeric(10, 4), nullable=True),
        sa.Column("gross_margin", sa.Numeric(10, 4), nullable=True),
        sa.Column("net_margin", sa.Numeric(10, 4), nullable=True),
        sa.Column("ebitda_margin", sa.Numeric(10, 4), nullable=True),
        sa.Column("debt_equity", sa.Numeric(10, 4), nullable=True),
        sa.Column("current_ratio", sa.Numeric(10, 4), nullable=True),
        sa.Column("interest_coverage", sa.Numeric(10, 4), nullable=True),
        sa.Column("fcf_yield", sa.Numeric(10, 4), nullable=True),
        sa.Column("fcf_per_share", sa.Numeric(10, 4), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(10, 4), nullable=True),
        sa.Column("payout_ratio", sa.Numeric(10, 4), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_metrics_ticker", "financial_metrics", ["ticker"])

    # technical_signals — hypertable (TimescaleDB)
    op.create_table(
        "technical_signals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("signal_type", sa.String(20), nullable=False),
        sa.Column("value", sa.Numeric(10, 4), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.Date(), nullable=False),
        sa.Column("timeframe", sa.String(5), server_default="1D", nullable=False),
        sa.Column("metadata", JSONB(), server_default="{}", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_technical_signals_ticker", "technical_signals", ["ticker"])
    op.create_index("ix_technical_signals_timestamp", "technical_signals", ["timestamp"])
    # Преобразуем в hypertable TimescaleDB
    op.execute("SELECT create_hypertable('technical_signals', 'timestamp', if_not_exists => TRUE);")

    # analyst_ratings
    op.create_table(
        "analyst_ratings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("analyst_firm", sa.String(100), nullable=False),
        sa.Column("rating", sa.String(20), nullable=False),
        sa.Column("target_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("rating_date", sa.Date(), nullable=False),
        sa.Column("previous_rating", sa.String(20), nullable=True),
        sa.Column("previous_target", sa.Numeric(10, 2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyst_ratings_ticker", "analyst_ratings", ["ticker"])
    op.create_index("ix_analyst_ratings_date", "analyst_ratings", ["rating_date"])


def downgrade() -> None:
    op.drop_table("analyst_ratings")
    op.drop_table("technical_signals")
    op.drop_table("financial_metrics")
    op.drop_table("financial_reports")
    op.drop_table("companies")
