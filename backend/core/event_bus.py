"""
backend/core/event_bus.py
Asynchronous pub/sub event bus for real-time WebSocket communication.
"""

import asyncio
from typing import Set, Dict, Any, Optional
import json
import time


class EventBus:
    """Thread-safe and async-compatible event bus."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._subscribers: Set[asyncio.Queue] = set()
            cls._instance._loop: Optional[asyncio.AbstractEventLoop] = None
        return cls._instance

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        """Subscribes an async queue to receive broadcast events."""
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """Removes a subscriber queue."""
        self._subscribers.discard(q)

    def publish_sync(self, event_type: str, data: Any) -> None:
        """
        Thread-safe synchronous publish from background workers or sync handlers.
        """
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.publish(event_type, data), self._loop)
        else:
            # Fallback for queues if loop is direct
            for q in list(self._subscribers):
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass

    async def publish(self, event_type: str, data: Any) -> None:
        """Asynchronously dispatches an event to all subscribers."""
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }

        dead_queues = []
        for q in self._subscribers:
            try:
                await q.put(payload)
            except Exception:
                dead_queues.append(q)

        for dq in dead_queues:
            self._subscribers.discard(dq)


def get_event_bus() -> EventBus:
    return EventBus()
