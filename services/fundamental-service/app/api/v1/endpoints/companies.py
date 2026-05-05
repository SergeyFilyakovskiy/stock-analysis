from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.companies import (
    CompanyReportSchema,
    CompanySchema,
    FinancialReportSchema,
    FinancialMetricsSchema,
    ValuationSchema,
    AnalystRatingSchema,
)
from app.application.queries.get_company_metrics import (
    GetCompanyMetricsHandler,
    GetCompanyMetricsQuery,
)
from app.application.queries.get_financial_reports import (
    GetFinancialReportsHandler,
    GetFinancialReportsQuery,
)
from app.builders.company_report_builder import CompanyReportBuilder
from app.core.dependencies import get_company_metrics_handler, get_financial_reports_handler, get_report_builder
from app.domain.exceptions import CompanyNotFoundError, MetricsNotFoundError
from app.valuation.dcf import DCFModel
from app.valuation.pe_relative import PERelativeModel
from app.valuation.ev_ebitda import EVEBITDAModel

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{ticker}", response_model=CompanySchema)
async def get_company(
    ticker: str,
    handler: GetCompanyMetricsHandler = Depends(get_company_metrics_handler),
) -> CompanySchema:
    try:
        result = await handler.handle(GetCompanyMetricsQuery(ticker=ticker.upper()))
        c = result.company
        return CompanySchema(
            ticker=c.ticker, name=c.name, sector=c.sector,
            industry=c.industry, market_cap=c.market_cap, country=c.country,
        )
    except CompanyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{ticker}/metrics", response_model=FinancialMetricsSchema)
async def get_metrics(
    ticker: str,
    handler: GetCompanyMetricsHandler = Depends(get_company_metrics_handler),
) -> FinancialMetricsSchema:
    try:
        result = await handler.handle(GetCompanyMetricsQuery(ticker=ticker.upper()))
        m = result.metrics
        return FinancialMetricsSchema(
            ticker=m.ticker, calculated_at=m.calculated_at,
            pe=m.pe, pb=m.pb, ps=m.ps, ev_ebitda=m.ev_ebitda,
            roe=m.roe, roa=m.roa, roic=m.roic,
            gross_margin=m.gross_margin, net_margin=m.net_margin,
            ebitda_margin=m.ebitda_margin, debt_equity=m.debt_equity,
            dividend_yield=m.dividend_yield,
        )
    except (CompanyNotFoundError, MetricsNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{ticker}/reports", response_model=list[FinancialReportSchema])
async def get_reports(
    ticker: str,
    limit: int = Query(8, ge=1, le=40),
    period_type: Optional[str] = Query(None, pattern="^(annual|quarterly)$"),
    handler: GetFinancialReportsHandler = Depends(get_financial_reports_handler),
) -> list[FinancialReportSchema]:
    try:
        reports = await handler.handle(
            GetFinancialReportsQuery(ticker=ticker.upper(), limit=limit, period_type=period_type)
        )
        return [
            FinancialReportSchema(
                period=r.period, period_type=r.period_type,
                fiscal_year=r.fiscal_year, fiscal_quarter=r.fiscal_quarter,
                revenue=r.revenue, net_income=r.net_income, ebitda=r.ebitda,
                free_cash_flow=r.free_cash_flow, eps_diluted=r.eps_diluted,
                source=r.source,
            )
            for r in reports
        ]
    except CompanyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{ticker}/report", response_model=CompanyReportSchema)
async def get_full_report(
    ticker: str,
    valuation_model: str = Query("dcf", pattern="^(dcf|pe|ev_ebitda)$"),
    builder: CompanyReportBuilder = Depends(get_report_builder),
) -> CompanyReportSchema:
    """Полный отчёт через Builder-паттерн."""
    model_map = {"dcf": DCFModel(), "pe": PERelativeModel(), "ev_ebitda": EVEBITDAModel()}
    try:
        report = await (
            builder(ticker.upper())
            .with_basic_info()
            .with_financial_metrics()
            .with_valuation(model_map[valuation_model])
            .with_analyst_ratings()
            .build()
        )
    except CompanyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return CompanyReportSchema(
        ticker=report.ticker,
        company=CompanySchema(**report.company.__dict__) if report.company else None,
        metrics=FinancialMetricsSchema(**{
            k: v for k, v in report.metrics.__dict__.items()
            if k in FinancialMetricsSchema.model_fields
        }) if report.metrics else None,
        reports=[FinancialReportSchema(**{k: v for k, v in r.__dict__.items() if k in FinancialReportSchema.model_fields}) for r in report.reports],
        valuations=[
            ValuationSchema(
                model_name=v.model_name,
                estimated_value=v.estimated_value,
                current_price=v.current_price,
                confidence_score=v.confidence_score,
                is_undervalued=v.is_undervalued,
                upside_pct=v.upside,
            )
            for v in report.valuations
        ],
        analyst_ratings=[
            AnalystRatingSchema(
                analyst_firm=r.analyst_firm, rating=r.rating,
                target_price=r.target_price, rating_date=r.rating_date,
            )
            for r in report.analyst_ratings
        ],
    )
