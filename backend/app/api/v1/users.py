"""User profile API routes."""

from __future__ import annotations

import os
import uuid
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, FileTypeError, FileSizeError
from app.core.security import hash_password, verify_password
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    MessageResponse,
    PasswordChange,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current user's profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the current user's profile."""
    repo = UserRepository(db)

    update_fields = {}
    if data.username is not None:
        # Check for duplicate
        existing = await repo.get_by_username(data.username)
        if existing and existing.id != user.id:
            from app.core.exceptions import ConflictError
            raise ConflictError("Username already taken")
        update_fields["username"] = data.username

    if data.email is not None:
        existing = await repo.get_by_email(data.email)
        if existing and existing.id != user.id:
            from app.core.exceptions import ConflictError
            raise ConflictError("Email already registered")
        update_fields["email"] = data.email

    if data.avatar_url is not None:
        update_fields["avatar_url"] = data.avatar_url

    updated = await repo.update(user, **update_fields)
    return UserResponse.model_validate(updated)


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Change the current user's password."""
    if not verify_password(data.current_password, user.password_hash):
        raise AuthenticationError(detail="Current password is incorrect")

    repo = UserRepository(db)
    new_hash = hash_password(data.new_password)
    await repo.update(user, password_hash=new_hash)

    return MessageResponse(message="Password changed successfully")


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Upload or replace profile avatar image."""
    # Validate content type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise FileTypeError([".jpg", ".jpeg", ".png", ".gif", ".webp"])

    data = await file.read()
    if len(data) > 5 * 1024 * 1024:  # 5 MB limit for avatars
        raise FileSizeError(5)

    # Save to uploads/avatars/<uuid>.<ext>
    ext = os.path.splitext(file.filename or "avatar.jpg")[1].lower() or ".jpg"
    avatars_dir = os.path.join(os.path.abspath(settings.UPLOAD_DIR), "avatars")
    os.makedirs(avatars_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(avatars_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(data)

    # Build a URL path served by the static mount
    avatar_url = f"/uploads/avatars/{filename}"

    repo = UserRepository(db)
    updated = await repo.update(user, avatar_url=avatar_url)
    return UserResponse.model_validate(updated)
