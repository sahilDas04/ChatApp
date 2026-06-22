"""Message API routes and WebSocket endpoint."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, is_token_blacklisted
from app.database.session import get_db, async_session_factory
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import MessageResponse
from app.schemas.message import MessageListResponse
from app.services.message_service import MessageService
from app.websocket.handlers import broadcast_user_status, handle_ws_message
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Messages"])


@router.post("/rooms/{room_id}/messages", status_code=201)
async def send_message(
    room_id: int,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a message to a room via REST (also broadcasts via WebSocket)."""
    content = (body.get("content") or "").strip()
    if not content:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    service = MessageService(db)
    message_out = await service.send_message(room_id, user.id, content)

    # Also broadcast to WebSocket clients in the room
    broadcast_data = {
        "type": "message",
        "data": {
            "id": message_out.id,
            "room_id": message_out.room_id,
            "sender_id": message_out.sender_id,
            "sender_username": user.username,
            "sender": {
                "id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
            },
            "content": message_out.content,
            "timestamp": message_out.timestamp.isoformat(),
        },
    }
    await manager.broadcast(room_id, broadcast_data)

    return broadcast_data["data"]


@router.delete("/rooms/{room_id}/messages/{message_id}", response_model=MessageResponse)
async def delete_message(
    room_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a message (sender, admin, or creator only)."""
    service = MessageService(db)
    await service.delete_message(room_id, message_id, user.id)

    # Broadcast deletion event so all clients remove the message immediately
    await manager.broadcast(room_id, {
        "type": "message_deleted",
        "data": {"message_id": message_id, "room_id": room_id},
    })
    return MessageResponse(message="Message deleted")


@router.get("/rooms/{room_id}/messages", response_model=MessageListResponse)
async def get_messages(
    room_id: int,
    before_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """Get message history for a room with cursor-based pagination."""
    service = MessageService(db)
    return await service.get_messages(room_id, user.id, before_id=before_id, limit=limit)


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
) -> None:
    """WebSocket endpoint for real-time room communication.

    Connect with: ws://host/ws/{room_id}?token=<access_token>
    """
    # ── Authenticate via query parameter token ────────────────────
    try:
        if is_token_blacklisted(token):
            await websocket.close(code=4001, reason="Token revoked")
            return

        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # ── Fetch username ────────────────────────────────────────────
    async with async_session_factory() as db:
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return
        username = user.username

    # ── Connect ───────────────────────────────────────────────────
    await manager.connect(room_id, user_id, websocket)

    # Broadcast online status
    await broadcast_user_status(room_id, user_id, username, "online")

    # Send list of currently online users
    online_users = manager.get_online_users(room_id)
    await manager.send_personal(room_id, user_id, {
        "type": "online_users",
        "data": {"users": online_users},
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            # Handle each message in its own DB session
            async with async_session_factory() as db:
                try:
                    await handle_ws_message(data, room_id, user_id, username, db)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(f"WS handler error: {e}")
                    await manager.send_personal(room_id, user_id, {
                        "type": "error",
                        "data": {"message": str(e)},
                    })
    except WebSocketDisconnect:
        logger.info(f"User {user_id} WebSocket disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.disconnect(room_id, user_id)
        await broadcast_user_status(room_id, user_id, username, "offline")
