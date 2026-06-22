"""File service — business logic for file upload/download/delete."""

from __future__ import annotations

import os
from typing import List, Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    FileSizeError,
    FileTypeError,
    NotFoundError,
)
from app.models.room_member import MemberRole
from app.repositories.file_repo import FileRepository
from app.schemas.auth import UserBrief
from app.schemas.file import FileListResponse, FileResponse
from app.services.room_service import RoomService
from app.services.storage import storage_backend


class FileService:
    """Handles file uploads, downloads, and deletions."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = FileRepository(db)
        self.room_service = RoomService(db)
        self.storage = storage_backend

    def _validate_file(self, filename: str, size: int) -> None:
        """Validate file extension and size."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.allowed_extensions_list:
            raise FileTypeError(settings.allowed_extensions_list)
        if size > settings.max_file_size_bytes:
            raise FileSizeError(settings.MAX_FILE_SIZE_MB)

    async def upload_file(
        self, room_id: int, user_id: int, upload: UploadFile
    ) -> FileResponse:
        """Upload a file to a room."""
        if not await self.room_service.is_member(room_id, user_id):
            raise AuthorizationError("You are not a member of this room")

        # Read file data
        data = await upload.read()
        filename = upload.filename or "untitled"
        content_type = upload.content_type

        # Validate
        self._validate_file(filename, len(data))

        # Store file
        relative_path = await self.storage.save(room_id, filename, data)

        # Save metadata
        file_record = await self.repo.create(
            room_id=room_id,
            uploaded_by=user_id,
            file_name=filename,
            file_path=relative_path,
            file_size=len(data),
            content_type=content_type,
        )

        return FileResponse(
            id=file_record.id,
            room_id=file_record.room_id,
            uploaded_by=file_record.uploaded_by,
            file_name=file_record.file_name,
            file_size=file_record.file_size,
            content_type=file_record.content_type,
            upload_time=file_record.upload_time,
        )

    async def get_files(self, room_id: int, user_id: int) -> FileListResponse:
        """List all files in a room."""
        if not await self.room_service.is_member(room_id, user_id):
            raise AuthorizationError("You are not a member of this room")

        files = await self.repo.get_room_files(room_id)
        total = await self.repo.get_room_file_count(room_id)

        items = []
        for f in files:
            uploader_brief = None
            if f.uploader:
                uploader_brief = UserBrief(
                    id=f.uploader.id,
                    username=f.uploader.username,
                    avatar_url=f.uploader.avatar_url,
                )
            items.append(FileResponse(
                id=f.id,
                room_id=f.room_id,
                uploaded_by=f.uploaded_by,
                uploader=uploader_brief,
                file_name=f.file_name,
                file_size=f.file_size,
                content_type=f.content_type,
                upload_time=f.upload_time,
            ))

        return FileListResponse(items=items, total=total)

    async def download_file(self, room_id: int, file_id: int, user_id: int) -> Tuple[bytes, str, str]:
        """Download a file. Returns (data, filename, content_type)."""
        if not await self.room_service.is_member(room_id, user_id):
            raise AuthorizationError("You are not a member of this room")

        file_record = await self.repo.get_by_id(file_id)
        if not file_record or file_record.room_id != room_id:
            raise NotFoundError("File")

        data = await self.storage.get(file_record.file_path)
        return data, file_record.file_name, file_record.content_type or "application/octet-stream"

    async def delete_file(self, room_id: int, file_id: int, user_id: int) -> None:
        """Delete a file (uploader, admin, or creator only)."""
        file_record = await self.repo.get_by_id(file_id)
        if not file_record or file_record.room_id != room_id:
            raise NotFoundError("File")

        # Check permission: uploader, admin, or creator
        member = await self.room_service.repo.get_member(room_id, user_id)
        if not member:
            raise AuthorizationError("You are not a member of this room")

        is_uploader = file_record.uploaded_by == user_id
        is_admin_or_creator = member.role in (MemberRole.CREATOR, MemberRole.ADMIN)

        if not is_uploader and not is_admin_or_creator:
            raise AuthorizationError("Only the uploader, admin, or creator can delete this file")

        # Delete from storage
        await self.storage.delete(file_record.file_path)

        # Delete metadata
        await self.repo.delete_file(file_record)
