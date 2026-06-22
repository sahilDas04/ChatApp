"""File repository — database operations for uploaded files."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.file import File


class FileRepository:
    """Encapsulates all file-metadata database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        room_id: int,
        uploaded_by: int,
        file_name: str,
        file_path: str,
        file_size: int,
        content_type: Optional[str] = None,
    ) -> File:
        file = File(
            room_id=room_id,
            uploaded_by=uploaded_by,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
        )
        self.db.add(file)
        await self.db.flush()
        await self.db.refresh(file)
        return file

    async def get_by_id(self, file_id: int) -> Optional[File]:
        result = await self.db.execute(
            select(File).options(selectinload(File.uploader)).where(File.id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_room_files(self, room_id: int) -> List[File]:
        result = await self.db.execute(
            select(File)
            .options(selectinload(File.uploader))
            .where(File.room_id == room_id)
            .order_by(File.upload_time.desc())
        )
        return list(result.scalars().all())

    async def get_room_file_count(self, room_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(File.room_id == room_id)
        )
        return result.scalar() or 0

    async def delete_file(self, file: File) -> None:
        await self.db.delete(file)
        await self.db.flush()
