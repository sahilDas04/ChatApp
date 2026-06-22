"""User model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    created_rooms = relationship("Room", back_populates="creator", lazy="selectin")
    memberships = relationship("RoomMember", back_populates="user", lazy="selectin")
    messages = relationship("Message", back_populates="sender", lazy="selectin")
    uploaded_files = relationship("File", back_populates="uploader", lazy="selectin")
    join_requests = relationship("JoinRequest", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
