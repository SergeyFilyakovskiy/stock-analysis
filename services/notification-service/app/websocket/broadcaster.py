import logging
from app.infrastructure.messaging.schemas import AlertTriggeredEvent, ReportPublishedEvent
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

async def broadcast_alert(event: AlertTriggeredEvent) -> None:
    await manager.send(event.user_id, {
        "type": "price_alert",
        "data": {
            "alert_id":      event.alert_id,
            "portfolio_id":  event.portfolio_id,
            "ticker":        event.ticker,
            "condition":     event.condition,
            "target_price":  event.target_price,
            "current_price": event.current_price,
            "occurred_at":   event.occurred_at,
        },
    })

async def broadcast_report(event: ReportPublishedEvent) -> None:
    await manager.send(event.user_id, {
        "type": "report_published",
        "data": {
            "portfolio_id": event.portfolio_id,
            "report_type":  event.report_type,
            "report_url":   event.report_url,
            "generated_at": event.generated_at,
        },
    })