import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import settings
from app.infrastructure.cache.redis_client import get_redis

router = APIRouter(prefix="/ws", tags=["stream"])

@router.websocket("/stream/{ticker}")
async def stream_ticker(ticker: str, websocket: WebSocket, token: str | None = None):

    await websocket.accept()

    redis   = await get_redis()
    pubsub  = redis.pubsub()
    channel = f"price:{ticker.upper()}"

    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                await websocket.send_text(message["data"])
            else:
                await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
