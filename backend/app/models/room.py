"""Room model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Room(Base):
    """Chat room."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    creator = relationship("User", back_populates="created_rooms", lazy="selectin")
    members = relationship(
        "RoomMember", back_populates="room", lazy="selectin", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="room", lazy="selectin", cascade="all, delete-orphan"
    )
    files = relationship(
        "File", back_populates="room", lazy="selectin", cascade="all, delete-orphan"
    )
    join_requests = relationship(
        "JoinRequest", back_populates="room", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Room id={self.id} name={self.name!r}>"
