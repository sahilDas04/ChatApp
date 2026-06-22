"""File upload/download/delete API tests."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFileUpload:
    """File upload tests."""

    async def test_upload_valid_file(self, auth_client: AsyncClient) -> None:
        # Create room
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "File Room"})
        room_id = create_resp.json()["id"]

        # Upload a text file
        files = {"file": ("test.txt", b"Hello World", "text/plain")}
        resp = await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_name"] == "test.txt"
        assert data["file_size"] == 11

    async def test_upload_invalid_type(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "File Room 2"})
        room_id = create_resp.json()["id"]

        files = {"file": ("virus.exe", b"malicious content", "application/x-executable")}
        resp = await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)
        assert resp.status_code == 415

    async def test_list_files(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "File List Room"})
        room_id = create_resp.json()["id"]

        # Upload a file
        files = {"file": ("doc.pdf", b"PDF content", "application/pdf")}
        await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["file_name"] == "doc.pdf"


@pytest.mark.asyncio
class TestFileDownload:
    """File download tests."""

    async def test_download_file(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "DL Room"})
        room_id = create_resp.json()["id"]

        content = b"Download me!"
        files = {"file": ("download.txt", content, "text/plain")}
        upload_resp = await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)
        file_id = upload_resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}/files/{file_id}/download")
        assert resp.status_code == 200
        assert resp.content == content


@pytest.mark.asyncio
class TestFileDelete:
    """File delete tests."""

    async def test_delete_own_file(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Del Room"})
        room_id = create_resp.json()["id"]

        files = {"file": ("delete_me.txt", b"temp", "text/plain")}
        upload_resp = await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)
        file_id = upload_resp.json()["id"]

        resp = await auth_client.delete(f"/api/v1/rooms/{room_id}/files/{file_id}")
        assert resp.status_code == 200

    async def test_download_deleted_file(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Ghost Room"})
        room_id = create_resp.json()["id"]

        files = {"file": ("gone.txt", b"bye", "text/plain")}
        upload_resp = await auth_client.post(f"/api/v1/rooms/{room_id}/files", files=files)
        file_id = upload_resp.json()["id"]

        await auth_client.delete(f"/api/v1/rooms/{room_id}/files/{file_id}")

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}/files/{file_id}/download")
        assert resp.status_code == 404
