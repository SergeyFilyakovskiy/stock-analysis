from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions import AlertNotFound
from app.infrastructure.db.unit_of_work import UnitOfWork


@dataclass
class DeletePriceAlertCommand:
    alert_id: UUID
    user_id: UUID


class DeletePriceAlertHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: DeletePriceAlertCommand) -> None:
        alerts = await self._uow.alerts.get_by_user(command.user_id)
        alert = next((a for a in alerts if a.id == command.alert_id), None)
        if not alert:
            raise AlertNotFound(str(command.alert_id))

        await self._uow.alerts.delete(command.alert_id)
        await self._uow.commit_with_events([])