from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import AnalystRating, FinancialMetrics, FinancialReport
from app.domain.interfaces.i_financial_repo import IFinancialRepo
from app.infrastructure.db.models import (
    AnalystRatingModel,
    FinancialMetricsModel,
    FinancialReportModel,
)


class FinancialRepo(IFinancialRepo):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Reports ──────────────────────────────────────────────────────────────

    async def get_reports(
        self,
        ticker: str,
        limit: int = 8,
        period_type: Optional[str] = None,
    ) -> list[FinancialReport]:
        stmt = (
            select(FinancialReportModel)
            .where(FinancialReportModel.ticker == ticker)
            .order_by(
                FinancialReportModel.fiscal_year.desc(),
                FinancialReportModel.fiscal_quarter.desc(),
            )
            .limit(limit)
        )
        if period_type:
            stmt = stmt.where(FinancialReportModel.period_type == period_type)
        result = await self._session.execute(stmt)
        return [self._report_to_entity(r) for r in result.scalars().all()]

    async def get_report(self, ticker: str, period: str) -> Optional[FinancialReport]:
        result = await self._session.execute(
            select(FinancialReportModel).where(
                and_(
                    FinancialReportModel.ticker == ticker,
                    FinancialReportModel.period == period,
                )
            )
        )
        row = result.scalar_one_or_none()
        return self._report_to_entity(row) if row else None

    async def save_report(self, report: FinancialReport) -> None:
        result = await self._session.execute(
            select(FinancialReportModel).where(
                and_(
                    FinancialReportModel.ticker == report.ticker,
                    FinancialReportModel.period == report.period,
                )
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FinancialReportModel()
            self._session.add(row)
        self._update_report_model(row, report)

    async def save_reports(self, reports: list[FinancialReport]) -> None:
        for report in reports:
            await self.save_report(report)

    # ── Metrics ──────────────────────────────────────────────────────────────

    async def get_metrics(self, ticker: str) -> Optional[FinancialMetrics]:
        result = await self._session.execute(
            select(FinancialMetricsModel).where(
                FinancialMetricsModel.ticker == ticker
            )
        )
        row = result.scalar_one_or_none()
        return self._metrics_to_entity(row) if row else None

    async def save_metrics(self, metrics: FinancialMetrics) -> None:
        result = await self._session.execute(
            select(FinancialMetricsModel).where(
                FinancialMetricsModel.ticker == metrics.ticker
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = FinancialMetricsModel()
            self._session.add(row)
        self._update_metrics_model(row, metrics)

    # ── Analyst Ratings ──────────────────────────────────────────────────────

    async def get_analyst_ratings(
        self, ticker: str, limit: int = 10
    ) -> list[AnalystRating]:
        result = await self._session.execute(
            select(AnalystRatingModel)
            .where(AnalystRatingModel.ticker == ticker)
            .order_by(AnalystRatingModel.rating_date.desc())
            .limit(limit)
        )
        return [self._rating_to_entity(r) for r in result.scalars().all()]

    async def save_analyst_rating(self, rating: AnalystRating) -> None:
        row = AnalystRatingModel()
        self._session.add(row)
        self._update_rating_model(row, rating)

    # ── Screener ─────────────────────────────────────────────────────────────

    async def screen(
        self,
        pe_max: Optional[float] = None,
        pe_min: Optional[float] = None,
        roe_min: Optional[float] = None,
        ev_ebitda_max: Optional[float] = None,
        debt_equity_max: Optional[float] = None,
        sector: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialMetrics]:
        stmt = select(FinancialMetricsModel)

        if pe_max is not None:
            stmt = stmt.where(FinancialMetricsModel.pe <= pe_max)
        if pe_min is not None:
            stmt = stmt.where(FinancialMetricsModel.pe >= pe_min)
        if roe_min is not None:
            stmt = stmt.where(FinancialMetricsModel.roe >= roe_min)
        if ev_ebitda_max is not None:
            stmt = stmt.where(FinancialMetricsModel.ev_ebitda <= ev_ebitda_max)
        if debt_equity_max is not None:
            stmt = stmt.where(FinancialMetricsModel.debt_equity <= debt_equity_max)

        # JOIN с companies для фильтра по sector
        if sector is not None:
            from app.infrastructure.db.models import CompanyModel
            stmt = stmt.join(
                CompanyModel,
                FinancialMetricsModel.ticker == CompanyModel.ticker,
            ).where(CompanyModel.sector == sector)

        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._metrics_to_entity(r) for r in result.scalars().all()]

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _report_to_entity(m: FinancialReportModel) -> FinancialReport:
        return FinancialReport(
            ticker=m.ticker, period=m.period, period_type=m.period_type,
            fiscal_year=m.fiscal_year, fiscal_quarter=m.fiscal_quarter,
            revenue=m.revenue, gross_profit=m.gross_profit,
            operating_income=m.operating_income, net_income=m.net_income,
            ebitda=m.ebitda, eps=m.eps, eps_diluted=m.eps_diluted,
            total_assets=m.total_assets, total_liabilities=m.total_liabilities,
            total_equity=m.total_equity, total_debt=m.total_debt,
            cash_and_equivalents=m.cash_and_equivalents,
            operating_cash_flow=m.operating_cash_flow,
            capital_expenditures=m.capital_expenditures,
            free_cash_flow=m.free_cash_flow,
            report_date=m.report_date, source=m.source,
        )

    @staticmethod
    def _update_report_model(m: FinancialReportModel, e: FinancialReport) -> None:
        for field in [
            "ticker", "period", "period_type", "fiscal_year", "fiscal_quarter",
            "revenue", "gross_profit", "operating_income", "net_income", "ebitda",
            "eps", "eps_diluted", "total_assets", "total_liabilities", "total_equity",
            "total_debt", "cash_and_equivalents", "operating_cash_flow",
            "capital_expenditures", "free_cash_flow", "report_date", "source",
        ]:
            setattr(m, field, getattr(e, field))

    @staticmethod
    def _metrics_to_entity(m: FinancialMetricsModel) -> FinancialMetrics:
        return FinancialMetrics(
            ticker=m.ticker, calculated_at=m.calculated_at,
            pe=m.pe, pb=m.pb, ps=m.ps, ev_ebitda=m.ev_ebitda,
            roe=m.roe, roa=m.roa, roic=m.roic,
            gross_margin=m.gross_margin, net_margin=m.net_margin,
            ebitda_margin=m.ebitda_margin, debt_equity=m.debt_equity,
            current_ratio=m.current_ratio, interest_coverage=m.interest_coverage,
            fcf_yield=m.fcf_yield, fcf_per_share=m.fcf_per_share,
            dividend_yield=m.dividend_yield, payout_ratio=m.payout_ratio,
        )

    @staticmethod
    def _update_metrics_model(m: FinancialMetricsModel, e: FinancialMetrics) -> None:
        for field in [
            "ticker", "calculated_at", "pe", "pb", "ps", "ev_ebitda",
            "roe", "roa", "roic", "gross_margin", "net_margin", "ebitda_margin",
            "debt_equity", "current_ratio", "interest_coverage",
            "fcf_yield", "fcf_per_share", "dividend_yield", "payout_ratio",
        ]:
            setattr(m, field, getattr(e, field))

    @staticmethod
    def _rating_to_entity(m: AnalystRatingModel) -> AnalystRating:
        return AnalystRating(
            ticker=m.ticker, analyst_firm=m.analyst_firm, rating=m.rating,
            target_price=m.target_price, rating_date=m.rating_date,
            previous_rating=m.previous_rating, previous_target=m.previous_target,
        )

    @staticmethod
    def _update_rating_model(m: AnalystRatingModel, e: AnalystRating) -> None:
        for field in [
            "ticker", "analyst_firm", "rating", "target_price",
            "rating_date", "previous_rating", "previous_target",
        ]:
            setattr(m, field, getattr(e, field))
