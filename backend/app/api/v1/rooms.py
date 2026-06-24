"""Room management API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.join_request import RequestStatus
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.room import (
    JoinRequestAction,
    JoinRequestResponse,
    RoleUpdate,
    RoomCreate,
    RoomListResponse,
    RoomMemberResponse,
    RoomResponse,
    RoomUpdate,
)
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomResponse:
    service = RoomService(db)
    return await service.create_room(data, user.id)


@router.get("", response_model=RoomListResponse)
async def list_rooms(
    search: Optional[str] = Query(None, max_length=100),
    my_rooms: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomListResponse:
    service = RoomService(db)
    return await service.list_rooms(
        user.id,
        search=search,
        my_rooms=my_rooms,
        page=page,
        size=size,
    )




@router.get("/me/requests", response_model=list[JoinRequestResponse])
async def get_my_pending_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JoinRequestResponse]:
    service = RoomService(db)
    return await service.get_user_pending_requests(user.id)




@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomResponse:
    service = RoomService(db)
    return await service.get_room(room_id, user.id)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomResponse:
    service = RoomService(db)
    return await service.update_room(room_id, data, user.id)


@router.delete("/{room_id}", response_model=MessageResponse)
async def delete_room(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = RoomService(db)
    await service.delete_room(room_id, user.id)
    return MessageResponse(message="Room deleted successfully")




@router.post("/{room_id}/join", response_model=MessageResponse)
async def join_room(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = RoomService(db)
    result = await service.join_room(room_id, user.id)
    return MessageResponse(message=result["message"])


@router.post("/{room_id}/leave", response_model=MessageResponse)
async def leave_room(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = RoomService(db)
    await service.leave_room(room_id, user.id)
    return MessageResponse(message="Left the room")


@router.get("/{room_id}/members", response_model=list[RoomMemberResponse])
async def get_members(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RoomMemberResponse]:
    service = RoomService(db)
    return await service.get_members(room_id, user.id)


@router.delete("/{room_id}/members/{target_user_id}", response_model=MessageResponse)
async def remove_member(
    room_id: int,
    target_user_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = RoomService(db)
    await service.remove_member(room_id, target_user_id, user.id)
    return MessageResponse(message="Member removed")


@router.put("/{room_id}/members/{target_user_id}/role", response_model=RoomMemberResponse)
async def update_member_role(
    room_id: int,
    target_user_id: int,
    data: RoleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomMemberResponse:
    service = RoomService(db)
    return await service.update_member_role(
        room_id,
        target_user_id,
        data.role,
        user.id,
    )



@router.get("/{room_id}/requests", response_model=list[JoinRequestResponse])
async def get_join_requests(
    room_id: int,
    status: Optional[RequestStatus] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JoinRequestResponse]:
    service = RoomService(db)
    return await service.get_join_requests(room_id, user.id, status)


@router.put("/{room_id}/requests/{request_id}", response_model=JoinRequestResponse)
async def handle_join_request(
    room_id: int,
    request_id: int,
    data: JoinRequestAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JoinRequestResponse:
    service = RoomService(db)
    return await service.handle_join_request(
        room_id,
        request_id,
        data.status,
        user.id,
    )