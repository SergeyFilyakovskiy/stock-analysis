import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str) -> None:
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # держим соединение, читаем пинги
    except WebSocketDisconnect:
        logger.info("WS disconnected: user=%s", user_id)
    except Exception:
        logger.exception("WS error: user=%s", user_id)
    finally:
        await manager.disconnect(user_id, websocket)