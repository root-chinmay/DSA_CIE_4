"""
backend/api/websocket_manager.py
WebSocket manager streaming real-time events to connected browser tabs.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import json
import asyncio
from backend.core.event_bus import get_event_bus
from backend.core.logger import AppLogger


class WebSocketManager:
    """Manages active browser WebSocket clients."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


ws_manager = WebSocketManager()


async def websocket_bridge_task():
    """Bridges internal EventBus async queue to WebSocket clients."""
    bus = get_event_bus()
    queue = bus.subscribe()
    while True:
        try:
            event = await queue.get()
            await ws_manager.broadcast(event)
        except asyncio.CancelledError:
            bus.unsubscribe(queue)
            break
        except Exception:
            await asyncio.sleep(0.1)
