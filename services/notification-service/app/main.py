import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.ws import router as ws_router
from app.core.config import settings
from app.infrastructure.messaging.price_alert_consumer import consume_alert_events
from app.infrastructure.messaging.report_consumer import consume_report_events
from app.websocket.broadcaster import broadcast_alert, broadcast_report
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    alert_task  = asyncio.create_task(consume_alert_events(broadcast_alert),  name="consumer:alert.triggered")
    report_task = asyncio.create_task(consume_report_events(broadcast_report), name="consumer:report.published")
    logger.info("Notification consumers started")
    yield
    # shutdown
    alert_task.cancel()
    report_task.cancel()
    await asyncio.gather(alert_task, report_task, return_exceptions=True)
    await manager.disconnect_all()

app = FastAPI(
    root_path="/notification-service",
    version="0.1.0",
    title=settings.app_name,
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(ws_router)
Instrumentator().instrument(app).expose(app)

@app.get("/", tags=["health"])
async def health():
    return {"status": "healthy", "service": settings.app_name, "active_ws_users": manager.active_users}