"""Room service — business logic for room management and access control."""

from __future__ import annotations

import math
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from app.models.join_request import JoinRequest, RequestStatus
from app.models.room import Room
from app.models.room_member import MemberRole, RoomMember
from app.repositories.room_repo import RoomRepository
from app.schemas.room import (
    JoinRequestResponse,
    RoleUpdate,
    RoomCreate,
    RoomListResponse,
    RoomMemberResponse,
    RoomResponse,
    RoomUpdate,
)
from app.schemas.auth import UserBrief


class RoomService:
    """Handles room CRUD, membership, and join requests."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = RoomRepository(db)
        self.db = db

    # ── Helpers ───────────────────────────────────────────────────

    async def _get_room_or_404(self, room_id: int) -> Room:
        room = await self.repo.get_by_id(room_id)
        if not room:
            raise NotFoundError("Room")
        return room

    async def _require_membership(self, room_id: int, user_id: int) -> RoomMember:
        member = await self.repo.get_member(room_id, user_id)
        if not member:
            raise AuthorizationError("You are not a member of this room")
        return member

    async def _require_admin(self, room_id: int, user_id: int) -> RoomMember:
        member = await self._require_membership(room_id, user_id)
        if member.role not in (MemberRole.CREATOR, MemberRole.ADMIN):
            raise AuthorizationError("Admin or creator privileges required")
        return member

    async def _require_creator(self, room_id: int, user_id: int) -> RoomMember:
        member = await self._require_membership(room_id, user_id)
        if member.role != MemberRole.CREATOR:
            raise AuthorizationError("Only the room creator can perform this action")
        return member

    def _room_to_response(self, room: Room, member_count: int = 0) -> RoomResponse:
        creator_brief = None
        if room.creator:
            creator_brief = UserBrief(
                id=room.creator.id,
                username=room.creator.username,
                avatar_url=room.creator.avatar_url,
            )
        return RoomResponse(
            id=room.id,
            name=room.name,
            description=room.description,
            creator_id=room.creator_id,
            creator=creator_brief,
            is_private=room.is_private,
            created_at=room.created_at,
            member_count=member_count,
        )

    # ── Room CRUD ─────────────────────────────────────────────────

    async def create_room(self, data: RoomCreate, creator_id: int) -> RoomResponse:
        room = await self.repo.create(
            name=data.name,
            description=data.description,
            creator_id=creator_id,
            is_private=data.is_private,
        )
        # Auto-add creator as member with creator role
        await self.repo.add_member(room.id, creator_id, MemberRole.CREATOR)
        # Refresh to get relationships
        room = await self._get_room_or_404(room.id)
        return self._room_to_response(room, member_count=1)

    async def get_room(self, room_id: int, user_id: int) -> RoomResponse:
        room = await self._get_room_or_404(room_id)
        if room.is_private:
            await self._require_membership(room_id, user_id)
        count = await self.repo.get_member_count(room_id)
        return self._room_to_response(room, member_count=count)

    async def list_rooms(
        self,
        user_id: int,
        search: Optional[str] = None,
        my_rooms: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> RoomListResponse:
        rooms, total = await self.repo.list_rooms(
            search=search, user_id=user_id, my_rooms=my_rooms, page=page, size=size
        )
        items = []
        for room in rooms:
            count = await self.repo.get_member_count(room.id)
            items.append(self._room_to_response(room, member_count=count))

        pages = math.ceil(total / size) if size > 0 else 0
        return RoomListResponse(items=items, total=total, page=page, size=size, pages=pages)

    async def update_room(self, room_id: int, data: RoomUpdate, user_id: int) -> RoomResponse:
        room = await self._get_room_or_404(room_id)
        await self._require_creator(room_id, user_id)
        updated = await self.repo.update(
            room,
            name=data.name,
            description=data.description,
            is_private=data.is_private,
        )
        count = await self.repo.get_member_count(room_id)
        return self._room_to_response(updated, member_count=count)

    async def delete_room(self, room_id: int, user_id: int) -> None:
        room = await self._get_room_or_404(room_id)
        await self._require_creator(room_id, user_id)
        await self.repo.delete(room)

    # ── Membership ────────────────────────────────────────────────

    async def join_room(self, room_id: int, user_id: int) -> dict:
        room = await self._get_room_or_404(room_id)

        # Already a member?
        existing = await self.repo.get_member(room_id, user_id)
        if existing:
            raise ConflictError("You are already a member of this room")

        if room.is_private:
            # Check for existing pending request
            pending = await self.repo.get_pending_request(room_id, user_id)
            if pending:
                raise ConflictError("You already have a pending request for this room")
            await self.repo.create_join_request(room_id, user_id)
            return {"message": "Join request submitted. Waiting for approval."}
        else:
            await self.repo.add_member(room_id, user_id, MemberRole.MEMBER)
            return {"message": "Successfully joined the room"}

    async def leave_room(self, room_id: int, user_id: int) -> None:
        member = await self._require_membership(room_id, user_id)
        if member.role == MemberRole.CREATOR:
            raise AuthorizationError("Room creator cannot leave. Delete the room instead.")
        await self.repo.remove_member(room_id, user_id)

    async def get_members(self, room_id: int, user_id: int) -> List[RoomMemberResponse]:
        await self._get_room_or_404(room_id)
        await self._require_membership(room_id, user_id)
        members = await self.repo.get_members(room_id)
        result = []
        for m in members:
            user_brief = UserBrief(id=m.user.id, username=m.user.username, avatar_url=m.user.avatar_url)
            result.append(RoomMemberResponse(
                id=m.id, user_id=m.user_id, user=user_brief, role=m.role, joined_at=m.joined_at
            ))
        return result

    async def remove_member(self, room_id: int, target_user_id: int, actor_id: int) -> None:
        await self._require_admin(room_id, actor_id)
        target = await self.repo.get_member(room_id, target_user_id)
        if not target:
            raise NotFoundError("Member")
        if target.role == MemberRole.CREATOR:
            raise AuthorizationError("Cannot remove the room creator")
        await self.repo.remove_member(room_id, target_user_id)

    async def update_member_role(
        self, room_id: int, target_user_id: int, role: MemberRole, actor_id: int
    ) -> RoomMemberResponse:
        await self._require_creator(room_id, actor_id)
        target = await self.repo.get_member(room_id, target_user_id)
        if not target:
            raise NotFoundError("Member")
        if target.role == MemberRole.CREATOR:
            raise AuthorizationError("Cannot change the creator's role")
        if role == MemberRole.CREATOR:
            raise AuthorizationError("Cannot assign creator role")
        updated = await self.repo.update_member_role(target, role)
        user_brief = UserBrief(id=updated.user.id, username=updated.user.username, avatar_url=updated.user.avatar_url)
        return RoomMemberResponse(
            id=updated.id, user_id=updated.user_id, user=user_brief, role=updated.role, joined_at=updated.joined_at
        )

    # ── Join Requests ─────────────────────────────────────────────

    async def get_join_requests(
        self, room_id: int, user_id: int, status: Optional[RequestStatus] = None
    ) -> List[JoinRequestResponse]:
        await self._require_admin(room_id, user_id)
        requests = await self.repo.get_room_requests(room_id, status)
        result = []
        for r in requests:
            user_brief = None
            if r.user:
                user_brief = UserBrief(id=r.user.id, username=r.user.username, avatar_url=r.user.avatar_url)
            result.append(JoinRequestResponse(
                id=r.id, room_id=r.room_id, user_id=r.user_id, user=user_brief,
                status=r.status, requested_at=r.requested_at
            ))
        return result

    async def handle_join_request(
        self, room_id: int, request_id: int, status: RequestStatus, actor_id: int
    ) -> JoinRequestResponse:
        await self._require_admin(room_id, actor_id)
        request = await self.repo.get_join_request(request_id)
        if not request or request.room_id != room_id:
            raise NotFoundError("Join request")

        if request.status != RequestStatus.PENDING:
            raise ConflictError(f"Request already {request.status.value}")

        updated = await self.repo.update_request_status(request, status)

        # If approved, add as member
        if status == RequestStatus.APPROVED:
            await self.repo.add_member(room_id, request.user_id, MemberRole.MEMBER)

        user_brief = None
        if updated.user:
            user_brief = UserBrief(id=updated.user.id, username=updated.user.username, avatar_url=updated.user.avatar_url)
        return JoinRequestResponse(
            id=updated.id, room_id=updated.room_id, user_id=updated.user_id,
            user=user_brief, status=updated.status, requested_at=updated.requested_at
        )

    async def get_user_pending_requests(self, user_id: int) -> List[JoinRequestResponse]:
        requests = await self.repo.get_user_pending_requests(user_id)
        return [
            JoinRequestResponse(
                id=r.id, room_id=r.room_id, user_id=r.user_id,
                status=r.status, requested_at=r.requested_at
            )
            for r in requests
        ]

    async def is_member(self, room_id: int, user_id: int) -> bool:
        """Check if user is a member of a room."""
        member = await self.repo.get_member(room_id, user_id)
        return member is not None
