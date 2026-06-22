"""File management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.file import FileListResponse, FileResponse
from app.services.file_service import FileService

router = APIRouter(tags=["Files"])


@router.post("/rooms/{room_id}/files", response_model=FileResponse, status_code=201)
async def upload_file(
    room_id: int,
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Upload a file to a room."""
    service = FileService(db)
    return await service.upload_file(room_id, user.id, file)


@router.get("/rooms/{room_id}/files", response_model=FileListResponse)
async def list_files(
    room_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileListResponse:
    """List all files in a room."""
    service = FileService(db)
    return await service.get_files(room_id, user.id)


@router.get("/rooms/{room_id}/files/{file_id}/download")
async def download_file(
    room_id: int,
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download a file from a room."""
    service = FileService(db)
    data, filename, content_type = await service.download_file(room_id, file_id, user.id)

    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.delete("/rooms/{room_id}/files/{file_id}", response_model=MessageResponse)
async def delete_file(
    room_id: int,
    file_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete a file (uploader/admin/creator only)."""
    service = FileService(db)
    await service.delete_file(room_id, file_id, user.id)
    return MessageResponse(message="File deleted successfully")
