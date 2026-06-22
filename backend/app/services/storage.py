"""Abstract storage backend with local filesystem implementation.

Designed for easy migration to S3 / MinIO — just implement the StorageBackend protocol.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable

import aiofiles

from app.core.config import settings


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol defining a file storage backend."""

    async def save(self, room_id: int, filename: str, data: bytes) -> str:
        """Save file and return the relative storage path."""
        ...

    async def get(self, file_path: str) -> bytes:
        """Retrieve file contents by path."""
        ...

    async def delete(self, file_path: str) -> None:
        """Delete a file by path."""
        ...

    def get_absolute_path(self, file_path: str) -> Path:
        """Get absolute filesystem path for a stored file."""
        ...


class LocalStorage:
    """Stores files on the local filesystem under uploads/<room_id>/."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, room_id: int, filename: str, data: bytes) -> str:
        """Save file to uploads/<room_id>/<filename>."""
        room_dir = self.base_dir / str(room_id)
        room_dir.mkdir(parents=True, exist_ok=True)

        # Avoid name collisions by appending counter
        target = room_dir / filename
        counter = 1
        stem = target.stem
        suffix = target.suffix
        while target.exists():
            target = room_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        async with aiofiles.open(target, "wb") as f:
            await f.write(data)

        # Return relative path from base_dir
        return str(target.relative_to(self.base_dir))

    async def get(self, file_path: str) -> bytes:
        """Read file from disk."""
        full_path = self.base_dir / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, file_path: str) -> None:
        """Delete file from disk."""
        full_path = self.base_dir / file_path
        if full_path.exists():
            full_path.unlink()

    def get_absolute_path(self, file_path: str) -> Path:
        """Get the absolute path for a stored file."""
        return self.base_dir / file_path


# Singleton instance — swap this for S3Storage / MinIOStorage later
storage_backend: LocalStorage = LocalStorage()
