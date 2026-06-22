"""Message API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestMessages:
    """Message history and sending tests."""

    async def test_get_messages_empty(self, auth_client: AsyncClient) -> None:
        # Create a room
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Msg Room"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_messages_not_member(self, auth_client: AsyncClient, client: AsyncClient) -> None:
        # Create room with auth_client
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Private Msg Room", "is_private": True})
        room_id = create_resp.json()["id"]

        # Register another user
        await client.post("/api/v1/auth/register", json={
            "username": "other_user",
            "email": "other@example.com",
            "password": "Other1Pass",
        })
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "other@example.com",
            "password": "Other1Pass",
        })
        other_token = login_resp.json()["access_token"]

        # Try to access messages
        resp = await client.get(
            f"/api/v1/rooms/{room_id}/messages",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

    async def test_get_messages_pagination(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Paginated Room"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.get(
            f"/api/v1/rooms/{room_id}/messages",
            params={"limit": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "has_more" in data
