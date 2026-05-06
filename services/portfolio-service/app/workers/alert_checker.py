import logging
from decimal import Decimal

from app.infrastructure.messaging.schemas import PriceUpdatedEvent
from app.infrastructure.db.session import AsyncSessionFactory
from app.infrastructure.db.repositories.alert_repo import AlertRepo
from app.infrastructure.outbox.outbox_repo import OutboxRepo
from app.infrastructure.db.models import OutboxEventModel
from app.domain.events import AlertTriggered

import json
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_alerts(event: PriceUpdatedEvent) -> None:
    """
    Вызывается из consumer при каждом price.updated.
    Проверяет активные алерты по тикеру и кладёт AlertTriggered в Outbox.
    """
    async with AsyncSessionFactory() as session:
        alert_repo = AlertRepo(session)
        outbox_repo = OutboxRepo(session)

        alerts = await alert_repo.get_active_by_ticker(event.ticker)
        if not alerts:
            return

        triggered = []
        for alert in alerts:
            hit = (
                alert.condition == "ABOVE" and event.price >= alert.target_price.amount
                or
                alert.condition == "BELOW" and event.price <= alert.target_price.amount
            )
            if hit:
                domain_event = AlertTriggered(
                    alert_id=alert.id,
                    portfolio_id=alert.portfolio_id,
                    user_id=alert.user_id,
                    ticker=str(alert.ticker),
                    condition=alert.condition,
                    target_price=alert.target_price.amount,
                    current_price=event.price,
                )
                session.add(
                    OutboxEventModel(
                        id=uuid4(),
                        event_type="AlertTriggered",
                        payload=json.dumps(domain_event.__dict__, default=str),
                        routing_key="portfolio.alert.triggered",
                    )
                )
                await alert_repo.deactivate(alert.id)
                triggered.append(alert.id)

        if triggered:
            await session.commit()
            logger.info("Triggered %d alerts for %s @ %s", len(triggered), event.ticker, event.price)