"""Room repository — database operations for rooms, members, and join requests."""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import delete, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.join_request import JoinRequest, RequestStatus
from app.models.room import Room
from app.models.room_member import MemberRole, RoomMember


class RoomRepository:
    """Encapsulates all room-related database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Room CRUD ─────────────────────────────────────────────────

    async def create(self, name: str, description: Optional[str], creator_id: int, is_private: bool) -> Room:
        room = Room(name=name, description=description, creator_id=creator_id, is_private=is_private)
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def get_by_id(self, room_id: int) -> Optional[Room]:
        result = await self.db.execute(
            select(Room).options(selectinload(Room.creator)).where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def update(self, room: Room, **kwargs: object) -> Room:
        for key, value in kwargs.items():
            if value is not None and hasattr(room, key):
                setattr(room, key, value)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def delete(self, room: Room) -> None:
        await self.db.delete(room)
        await self.db.flush()

    async def list_rooms(
        self,
        search: Optional[str] = None,
        user_id: Optional[int] = None,
        my_rooms: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Room], int]:
        """List rooms with optional filters and pagination."""
        query = select(Room).options(selectinload(Room.creator))

        if search:
            pattern = f"%{search}%"
            query = query.where(or_(Room.name.ilike(pattern), Room.description.ilike(pattern)))

        if my_rooms and user_id:
            # Rooms where user is a member
            query = query.join(RoomMember, RoomMember.room_id == Room.id).where(
                RoomMember.user_id == user_id
            )
        elif not my_rooms:
            # Public rooms + rooms user is member of
            if user_id:
                subq = select(RoomMember.room_id).where(RoomMember.user_id == user_id)
                query = query.where(or_(Room.is_private == False, Room.id.in_(subq)))  # noqa: E712
            else:
                query = query.where(Room.is_private == False)  # noqa: E712

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(Room.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        rooms = list(result.scalars().all())

        return rooms, total

    # ── Membership ────────────────────────────────────────────────

    async def add_member(self, room_id: int, user_id: int, role: MemberRole = MemberRole.MEMBER) -> RoomMember:
        member = RoomMember(room_id=room_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def get_member(self, room_id: int, user_id: int) -> Optional[RoomMember]:
        result = await self.db.execute(
            select(RoomMember)
            .options(selectinload(RoomMember.user))
            .where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_members(self, room_id: int) -> List[RoomMember]:
        result = await self.db.execute(
            select(RoomMember)
            .options(selectinload(RoomMember.user))
            .where(RoomMember.room_id == room_id)
            .order_by(RoomMember.joined_at)
        )
        return list(result.scalars().all())

    async def update_member_role(self, member: RoomMember, role: MemberRole) -> RoomMember:
        member.role = role
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, room_id: int, user_id: int) -> None:
        await self.db.execute(
            delete(RoomMember).where(
                RoomMember.room_id == room_id, RoomMember.user_id == user_id
            )
        )
        await self.db.flush()

    async def get_member_count(self, room_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(RoomMember.room_id == room_id)
        )
        return result.scalar() or 0

    # ── Join Requests ─────────────────────────────────────────────

    async def create_join_request(self, room_id: int, user_id: int) -> JoinRequest:
        request = JoinRequest(room_id=room_id, user_id=user_id)
        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def get_join_request(self, request_id: int) -> Optional[JoinRequest]:
        result = await self.db.execute(
            select(JoinRequest).options(selectinload(JoinRequest.user)).where(JoinRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_request(self, room_id: int, user_id: int) -> Optional[JoinRequest]:
        result = await self.db.execute(
            select(JoinRequest).where(
                JoinRequest.room_id == room_id,
                JoinRequest.user_id == user_id,
                JoinRequest.status == RequestStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get_room_requests(self, room_id: int, status: Optional[RequestStatus] = None) -> List[JoinRequest]:
        query = select(JoinRequest).options(selectinload(JoinRequest.user)).where(JoinRequest.room_id == room_id)
        if status:
            query = query.where(JoinRequest.status == status)
        query = query.order_by(JoinRequest.requested_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_pending_requests(self, user_id: int) -> List[JoinRequest]:
        """Get all pending requests by a user (across all rooms)."""
        result = await self.db.execute(
            select(JoinRequest)
            .options(selectinload(JoinRequest.room))
            .where(JoinRequest.user_id == user_id, JoinRequest.status == RequestStatus.PENDING)
            .order_by(JoinRequest.requested_at.desc())
        )
        return list(result.scalars().all())

    async def update_request_status(self, request: JoinRequest, status: RequestStatus) -> JoinRequest:
        request.status = status
        await self.db.flush()
        await self.db.refresh(request)
        return request
