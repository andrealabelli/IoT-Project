import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.connections[device_id].append(websocket)

    async def disconnect(self, device_id: str, websocket: WebSocket):
        async with self.lock:
            if websocket in self.connections[device_id]:
                self.connections[device_id].remove(websocket)

    async def publish(self, device_id: str, data: dict[str, Any]):
        to_remove = []
        for ws in self.connections[device_id]:
            try:
                await ws.send_json(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            await self.disconnect(device_id, ws)


manager = ConnectionManager()
