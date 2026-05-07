import asyncio
import logging
from collections import defaultdict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    In-memory хранилище WS-соединений.
    Один user_id может иметь несколько вкладок/соединений.
    """
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send(self, user_id: str, payload: dict) -> None:
        sockets = set(self._connections.get(user_id, set()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                logger.warning("Dead socket for user=%s, removing", user_id)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[user_id].discard(ws)
                if not self._connections.get(user_id):
                    self._connections.pop(user_id, None)

    async def disconnect_all(self) -> None:
        """Graceful shutdown."""
        async with self._lock:
            all_sockets = [ws for s in self._connections.values() for ws in s]
            self._connections.clear()
        for ws in all_sockets:
            try:
                await ws.send_json({"type": "server_shutdown"})
                await ws.close()
            except Exception:
                pass

    @property
    def active_users(self) -> int:
        return len(self._connections)

manager = ConnectionManager()