from fastapi import APIRouter, Depends

from app.api.v1.schemas.companies import CompareRequestSchema, CompanyReportSchema, CompanySchema, FinancialMetricsSchema
from app.application.queries.compare_companies import CompareCompaniesHandler, CompareCompaniesQuery
from app.core.dependencies import get_compare_handler

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=list[CompanyReportSchema])
async def compare_companies(
    body: CompareRequestSchema,
    handler: CompareCompaniesHandler = Depends(get_compare_handler),
) -> list[CompanyReportSchema]:
    reports = await handler.handle(
        CompareCompaniesQuery(
            tickers=[t.upper() for t in body.tickers],
            include_valuation=body.include_valuation,
        )
    )
    result = []
    for r in reports:
        result.append(CompanyReportSchema(
            ticker=r.ticker,
            company=CompanySchema(**r.company.__dict__) if r.company else None,
            metrics=FinancialMetricsSchema(**{k: v for k, v in r.metrics.__dict__.items() if k in FinancialMetricsSchema.model_fields}) if r.metrics else None,
        ))
    return result
