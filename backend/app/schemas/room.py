"""Room-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.room_member import MemberRole
from app.models.join_request import RequestStatus
from app.schemas.auth import UserBrief


# ── Request Schemas ───────────────────────────────────────────────────


class RoomCreate(BaseModel):
    """Create room request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: bool = False


class RoomUpdate(BaseModel):
    """Update room request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: Optional[bool] = None


class RoleUpdate(BaseModel):
    """Change member role request."""

    role: MemberRole


class JoinRequestAction(BaseModel):
    """Approve / reject a join request."""

    status: RequestStatus


# ── Response Schemas ──────────────────────────────────────────────────


class RoomResponse(BaseModel):
    """Room detail response."""

    id: int
    name: str
    description: Optional[str] = None
    creator_id: int
    creator: Optional[UserBrief] = None
    is_private: bool
    created_at: datetime
    member_count: Optional[int] = None

    model_config = {"from_attributes": True}


class RoomListResponse(BaseModel):
    """Paginated room list."""

    items: List[RoomResponse]
    total: int
    page: int
    size: int
    pages: int


class RoomMemberResponse(BaseModel):
    """Room member info."""

    id: int
    user_id: int
    user: UserBrief
    role: MemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class JoinRequestResponse(BaseModel):
    """Join request info."""

    id: int
    room_id: int
    user_id: int
    user: Optional[UserBrief] = None
    status: RequestStatus
    requested_at: datetime

    model_config = {"from_attributes": True}
