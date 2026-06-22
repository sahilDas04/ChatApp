"""Message service — business logic for chat messages."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.repositories.message_repo import MessageRepository
from app.schemas.auth import UserBrief
from app.schemas.message import MessageListResponse, MessageOut
from app.services.room_service import RoomService


class MessageService:
    """Handles sending and retrieving messages."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = MessageRepository(db)
        self.room_service = RoomService(db)

    async def send_message(self, room_id: int, sender_id: int, content: str) -> MessageOut:
        """Send a message to a room (validates membership)."""
        if not await self.room_service.is_member(room_id, sender_id):
            raise AuthorizationError("You are not a member of this room")

        message = await self.repo.create(room_id, sender_id, content)

        sender_brief = None
        if message.sender:
            sender_brief = UserBrief(
                id=message.sender.id,
                username=message.sender.username,
                avatar_url=message.sender.avatar_url,
            )

        return MessageOut(
            id=message.id,
            room_id=message.room_id,
            sender_id=message.sender_id,
            sender=sender_brief,
            content=message.content,
            is_read=message.is_read,
            timestamp=message.timestamp,
        )

    async def get_messages(
        self,
        room_id: int,
        user_id: int,
        before_id: Optional[int] = None,
        limit: int = 50,
    ) -> MessageListResponse:
        """Get message history for a room (validates membership)."""
        if not await self.room_service.is_member(room_id, user_id):
            raise AuthorizationError("You are not a member of this room")

        messages, total = await self.repo.get_messages(room_id, before_id, limit)

        items = []
        for m in messages:
            sender_brief = None
            if m.sender:
                sender_brief = UserBrief(
                    id=m.sender.id,
                    username=m.sender.username,
                    avatar_url=m.sender.avatar_url,
                )
            items.append(MessageOut(
                id=m.id,
                room_id=m.room_id,
                sender_id=m.sender_id,
                sender=sender_brief,
                content=m.content,
                is_read=m.is_read,
                timestamp=m.timestamp,
            ))

        has_more = len(messages) == limit
        return MessageListResponse(items=items, total=total, has_more=has_more)

    async def mark_read(self, message_id: int, user_id: int) -> None:
        """Mark a message as read."""
        message = await self.repo.get_by_id(message_id)
        if message:
            if not await self.room_service.is_member(message.room_id, user_id):
                raise AuthorizationError("You are not a member of this room")
            await self.repo.mark_as_read(message_id, user_id)

    async def delete_message(self, room_id: int, message_id: int, user_id: int) -> None:
        """Delete a message. Only the sender OR an admin/creator can delete."""
        message = await self.repo.get_by_id(message_id)
        if not message or message.room_id != room_id:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Message")

        # Check membership and role
        member = await self.room_service.repo.get_member(room_id, user_id)
        if not member:
            raise AuthorizationError("You are not a member of this room")

        from app.models.room_member import MemberRole
        is_sender = message.sender_id == user_id
        is_admin = member.role in (MemberRole.CREATOR, MemberRole.ADMIN)

        if not is_sender and not is_admin:
            raise AuthorizationError("You can only delete your own messages")

        await self.repo.delete(message)

