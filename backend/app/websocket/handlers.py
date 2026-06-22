"""WebSocket event handlers."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.message_service import MessageService
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


async def handle_ws_message(
    data: dict[str, Any],
    room_id: int,
    user_id: int,
    username: str,
    db: AsyncSession,
) -> None:
    """Route incoming WebSocket messages by type."""
    msg_type = data.get("type", "")

    if msg_type == "message":
        await _handle_chat_message(data, room_id, user_id, username, db)
    elif msg_type == "typing":
        await _handle_typing(data, room_id, user_id, username)
    elif msg_type == "read_receipt":
        await _handle_read_receipt(data, room_id, user_id, db)
    elif msg_type == "ping":
        # Keep-alive ping — respond with pong
        await manager.send_personal(room_id, user_id, {"type": "pong"})
    else:
        logger.warning(f"Unknown WS message type: {msg_type} from user {user_id}")


async def _handle_chat_message(
    data: dict[str, Any],
    room_id: int,
    user_id: int,
    username: str,
    db: AsyncSession,
) -> None:
    """Persist and broadcast a chat message."""
    content = data.get("content", "").strip()
    if not content:
        return

    svc = MessageService(db)
    message_out = await svc.send_message(room_id, user_id, content)

    # Broadcast to all users in the room
    broadcast_data = {
        "type": "message",
        "data": {
            "id": message_out.id,
            "room_id": message_out.room_id,
            "sender_id": message_out.sender_id,
            "sender_username": username,
            "content": message_out.content,
            "timestamp": message_out.timestamp.isoformat(),
        },
    }
    await manager.broadcast(room_id, broadcast_data)


async def _handle_typing(
    data: dict[str, Any],
    room_id: int,
    user_id: int,
    username: str,
) -> None:
    """Broadcast typing indicator to other users in the room."""
    is_typing = data.get("is_typing", False)
    broadcast_data = {
        "type": "typing",
        "data": {
            "user_id": user_id,
            "username": username,
            "is_typing": is_typing,
        },
    }
    await manager.broadcast(room_id, broadcast_data, exclude_user=user_id)


async def _handle_read_receipt(
    data: dict[str, Any],
    room_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    """Mark a message as read and notify the sender."""
    message_id = data.get("message_id")
    if not message_id:
        return

    svc = MessageService(db)
    await svc.mark_read(message_id, user_id)

    broadcast_data = {
        "type": "read_receipt",
        "data": {
            "message_id": message_id,
            "user_id": user_id,
        },
    }
    await manager.broadcast(room_id, broadcast_data, exclude_user=user_id)


async def broadcast_user_status(room_id: int, user_id: int, username: str, status: str) -> None:
    """Broadcast user online/offline status to a room."""
    broadcast_data = {
        "type": "user_status",
        "data": {
            "user_id": user_id,
            "username": username,
            "status": status,
        },
    }
    await manager.broadcast(room_id, broadcast_data, exclude_user=user_id)
