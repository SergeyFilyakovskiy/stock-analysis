from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.entities import Company
from app.domain.interfaces.i_company_repo import ICompanyRepo
from app.domain.interfaces.i_financial_repo import IFinancialRepo
from app.infrastructure.cache.valuation_cache import ValuationCache
from app.infrastructure.external.facade import FinancialDataFacade
from app.infrastructure.messaging.publisher import ReportPublisher

logger = logging.getLogger(__name__)


@dataclass
class ImportFinancialReportCommand:
    ticker: str
    force_refresh: bool = False


class ImportFinancialReportHandler:
    """
    Импортирует финансовые отчёты из Polygon / Alpha Vantage.
    Вызывается:
      - Celery beat (каждую ночь в 02:00 UTC) для всех тикеров
      - Триггерно при price.updated от market-service (новый тикер)
    """

    def __init__(
        self,
        company_repo: ICompanyRepo,
        financial_repo: IFinancialRepo,
        facade: FinancialDataFacade,
        publisher: ReportPublisher,
        valuation_cache: ValuationCache,
    ) -> None:
        self._company_repo = company_repo
        self._financial_repo = financial_repo
        self._facade = facade
        self._publisher = publisher
        self._valuation_cache = valuation_cache

    async def handle(self, command: ImportFinancialReportCommand) -> int:
        """Возвращает количество сохранённых/обновлённых отчётов."""
        ticker = command.ticker.upper()
        logger.info("Importing financials for %s", ticker)

        # Получаем данные компании (если нет — создаём)
        if not await self._company_repo.exists(ticker):
            details = await self._facade.get_company_details(ticker)
            company = Company(
                ticker=ticker,
                name=details.get("name", ticker),
                sector=details.get("sic_description", "Unknown"),
                industry=details.get("sic_description", "Unknown"),
                market_cap=None,
                country=details.get("locale", "US").upper(),
                description=details.get("description"),
            )
            await self._company_repo.save(company)
            logger.info("Created company record for %s", ticker)

        # Импорт годовых и квартальных отчётов параллельно
        import asyncio
        annual_task = self._facade.get_financials(ticker, limit=5, period_type="annual")
        quarterly_task = self._facade.get_financials(ticker, limit=12, period_type="quarterly")
        annual_reports, quarterly_reports = await asyncio.gather(
            annual_task, quarterly_task, return_exceptions=True
        )

        saved = 0
        for reports in (annual_reports, quarterly_reports):
            if isinstance(reports, Exception):
                logger.warning("Failed to fetch reports: %s", reports)
                continue
            if reports:
                await self._financial_repo.save_reports(reports)
                saved += len(reports)

        if saved > 0:
            # Инвалидируем кэш валюации — данные устарели
            await self._valuation_cache.invalidate(ticker)

            # Публикуем событие → notification-service → WebSocket
            latest = (annual_reports or quarterly_reports)
            if not isinstance(latest, Exception) and latest:
                last = latest[0]
                await self._publisher.publish_report_imported(
                    ticker=ticker,
                    period=last.period,
                    fiscal_year=last.fiscal_year,
                    source=last.source,
                )

        logger.info("Imported %d reports for %s", saved, ticker)
        return saved
