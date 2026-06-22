"""JoinRequest model and status enum."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RequestStatus(str, enum.Enum):
    """Status of a join request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class JoinRequest(Base):
    """Request to join a private room."""

    __tablename__ = "join_requests"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_join_request"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    room = relationship("Room", back_populates="join_requests")
    user = relationship("User", back_populates="join_requests")

    def __repr__(self) -> str:
        return f"<JoinRequest room={self.room_id} user={self.user_id} status={self.status.value}>"
