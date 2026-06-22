"""Message schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import UserBrief


class MessageCreate(BaseModel):
    """Create message request."""

    content: str = Field(..., min_length=1, max_length=5000)


class MessageOut(BaseModel):
    """Single message response."""

    id: int
    room_id: int
    sender_id: int
    sender: Optional[UserBrief] = None
    content: str
    is_read: bool
    timestamp: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """Paginated message list."""

    items: List[MessageOut]
    total: int
    has_more: bool


# ── WebSocket Event Schemas ──────────────────────────────────────────


class WSMessage(BaseModel):
    """WebSocket message payload."""

    type: str  # "message", "typing", "read_receipt", "user_status"
    data: dict


class TypingEvent(BaseModel):
    """Typing indicator payload."""

    room_id: int
    user_id: int
    username: str
    is_typing: bool


class ReadReceipt(BaseModel):
    """Read receipt payload."""

    room_id: int
    user_id: int
    message_id: int


class UserStatusEvent(BaseModel):
    """Online/offline status event."""

    user_id: int
    username: str
    status: str  # "online" or "offline"
