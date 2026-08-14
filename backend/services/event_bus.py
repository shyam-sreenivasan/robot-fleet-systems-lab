import asyncio
from typing import Set

from fastapi import WebSocket


class EventBus:
    """
    Very small in-memory WebSocket event broadcaster.

    V1 responsibility:
    - Track connected dashboard clients
    - Broadcast backend events to them
    """

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._loop = None

    def set_event_loop(self, loop):
        self._loop = loop

    async def connect(
        self,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self._connections.add(
            websocket
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):
        self._connections.discard(
            websocket
        )

    async def broadcast(
        self,
        event: dict,
    ):
        dead_connections = []

        for websocket in list(
            self._connections
        ):
            try:
                await websocket.send_json(
                    event
                )

            except Exception:
                dead_connections.append(
                    websocket
                )

        for websocket in dead_connections:
            self.disconnect(
                websocket
            )

    def publish(
        self,
        event: dict,
    ):
        """
        Thread-safe entry point for backend services such
        as HealthMonitor, which runs in a background thread.
        """

        if self._loop is None:
            return

        asyncio.run_coroutine_threadsafe(
            self.broadcast(event),
            self._loop,
        )