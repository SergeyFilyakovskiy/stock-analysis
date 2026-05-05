import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _build_handler():
    """Собирает ImportFinancialReportHandler с реальными зависимостями."""
    from app.application.commands.import_financial_report import ImportFinancialReportHandler
    from app.infrastructure.cache.valuation_cache import ValuationCache
    from app.infrastructure.db.repositories.company_repo import CompanyRepo
    from app.infrastructure.db.repositories.financial_repo import FinancialRepo
    from app.infrastructure.db.session import AsyncSessionFactory
    from app.infrastructure.external.facade import FinancialDataFacade
    from app.infrastructure.messaging.publisher import ReportPublisher

    publisher = ReportPublisher()
    await publisher.connect()

    async with AsyncSessionFactory() as session:
        return ImportFinancialReportHandler(
            company_repo=CompanyRepo(session),
            financial_repo=FinancialRepo(session),
            facade=FinancialDataFacade(),
            publisher=publisher,
            valuation_cache=ValuationCache(),
        ), session, publisher


@celery_app.task(
    name="app.workers.report_importer.import_financial_report_for_ticker",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,          # exponential backoff: 1s, 2s, 4s
    retry_backoff_max=60,
    retry_jitter=True,
)
def import_financial_report_for_ticker(self, ticker: str) -> dict:
    """Триггерная задача: импорт отчётов для одного тикера."""
    async def _run():
        from app.application.commands.import_financial_report import ImportFinancialReportCommand
        handler, session, publisher = await _build_handler()
        try:
            saved = await handler.handle(ImportFinancialReportCommand(ticker=ticker))
            await session.commit()
            return {"ticker": ticker, "saved": saved}
        finally:
            await publisher.close()
            await session.close()

    return asyncio.run(_run())


@celery_app.task(name="app.workers.report_importer.import_all_tickers")
def import_all_tickers() -> dict:
    """Ночной cron: обновляет отчёты для всех известных тикеров."""
    async def _run():
        from app.infrastructure.db.repositories.company_repo import CompanyRepo
        from app.infrastructure.db.session import AsyncSessionFactory

        async with AsyncSessionFactory() as session:
            tickers = await CompanyRepo(session).get_all_tickers()

        logger.info("Nightly import: %d tickers", len(tickers))
        for ticker in tickers:
            import_financial_report_for_ticker.delay(ticker) # type: ignore
        return {"queued": len(tickers)}

    return asyncio.run(_run())
