"""Message repository — database operations for chat messages."""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import Message


class MessageRepository:
    """Encapsulates all message-related database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, room_id: int, sender_id: int, content: str) -> Message:
        message = Message(room_id=room_id, sender_id=sender_id, content=content)
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        # Eagerly load sender
        result = await self.db.execute(
            select(Message).options(selectinload(Message.sender)).where(Message.id == message.id)
        )
        return result.scalar_one()

    async def get_messages(
        self,
        room_id: int,
        before_id: Optional[int] = None,
        limit: int = 50,
    ) -> Tuple[List[Message], int]:
        """Get messages for a room with cursor-based pagination."""
        query = (
            select(Message)
            .options(selectinload(Message.sender))
            .where(Message.room_id == room_id)
        )

        if before_id:
            query = query.where(Message.id < before_id)

        # Total count for the room
        count_result = await self.db.execute(
            select(func.count()).where(Message.room_id == room_id)
        )
        total = count_result.scalar() or 0

        query = query.order_by(Message.timestamp.desc()).limit(limit)
        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Return in chronological order
        messages.reverse()
        return messages, total

    async def mark_as_read(self, message_id: int, user_id: int) -> None:
        """Mark a message as read (simplified: sets is_read flag)."""
        await self.db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(is_read=True)
        )
        await self.db.flush()

    async def get_by_id(self, message_id: int) -> Optional[Message]:
        result = await self.db.execute(
            select(Message).options(selectinload(Message.sender)).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, message: Message) -> None:
        """Permanently delete a message."""
        await self.db.delete(message)
        await self.db.flush()

