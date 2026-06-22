"""File schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.auth import UserBrief


class FileResponse(BaseModel):
    """Uploaded file metadata response."""

    id: int
    room_id: int
    uploaded_by: int
    uploader: Optional[UserBrief] = None
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    upload_time: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """List of files in a room."""

    items: List[FileResponse]
    total: int
