"""Scalable WebSocket Connection Manager."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections across rooms.

    Structure: room_id → {user_id → WebSocket}
    """

    def __init__(self) -> None:
        # room_id -> {user_id -> WebSocket}
        self._connections: Dict[int, Dict[int, WebSocket]] = {}
        # Track online users globally: user_id -> set of room_ids
        self._user_rooms: Dict[int, Set[int]] = {}

    async def connect(self, room_id: int, user_id: int, websocket: WebSocket) -> None:
        """Register a connection and broadcast user online status."""
        await websocket.accept()

        if room_id not in self._connections:
            self._connections[room_id] = {}
        self._connections[room_id][user_id] = websocket

        if user_id not in self._user_rooms:
            self._user_rooms[user_id] = set()
        self._user_rooms[user_id].add(room_id)

        logger.info(f"User {user_id} connected to room {room_id}")

    async def disconnect(self, room_id: int, user_id: int) -> None:
        """Remove a connection and broadcast user offline status."""
        if room_id in self._connections:
            self._connections[room_id].pop(user_id, None)
            if not self._connections[room_id]:
                del self._connections[room_id]

        if user_id in self._user_rooms:
            self._user_rooms[user_id].discard(room_id)
            if not self._user_rooms[user_id]:
                del self._user_rooms[user_id]

        logger.info(f"User {user_id} disconnected from room {room_id}")

    async def broadcast(self, room_id: int, message: dict[str, Any], exclude_user: int | None = None) -> None:
        """Send a message to all connected users in a room."""
        if room_id not in self._connections:
            return

        disconnected = []
        for uid, ws in self._connections[room_id].items():
            if uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(uid)
                logger.warning(f"Failed to send to user {uid} in room {room_id}")

        # Clean up broken connections
        for uid in disconnected:
            await self.disconnect(room_id, uid)

    async def send_personal(self, room_id: int, user_id: int, message: dict[str, Any]) -> None:
        """Send a message to a specific user in a room."""
        ws = self._connections.get(room_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(room_id, user_id)

    def get_online_users(self, room_id: int) -> list[int]:
        """Get list of user IDs currently connected to a room."""
        return list(self._connections.get(room_id, {}).keys())

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is connected to any room."""
        return user_id in self._user_rooms and len(self._user_rooms[user_id]) > 0

    def get_room_connection_count(self, room_id: int) -> int:
        """Get number of active connections in a room."""
        return len(self._connections.get(room_id, {}))


# Global singleton
manager = ConnectionManager()
