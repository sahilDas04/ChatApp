"""Room management API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRoomCRUD:
    """Room creation, listing, update, delete tests."""

    async def test_create_room(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.post("/api/v1/rooms", json={
            "name": "Test Room",
            "description": "A test room",
            "is_private": False,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Room"
        assert data["member_count"] == 1

    async def test_list_my_rooms(self, auth_client: AsyncClient) -> None:
        # Create a room first
        await auth_client.post("/api/v1/rooms", json={"name": "My Room"})

        resp = await auth_client.get("/api/v1/rooms", params={"my_rooms": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_room(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Detail Room"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Detail Room"

    async def test_update_room(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Old Name"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.put(f"/api/v1/rooms/{room_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_delete_room(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Delete Me"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.delete(f"/api/v1/rooms/{room_id}")
        assert resp.status_code == 200

        # Verify deleted
        resp = await auth_client.get(f"/api/v1/rooms/{room_id}")
        assert resp.status_code == 404

    async def test_search_rooms(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/rooms", json={"name": "Python Developers"})
        await auth_client.post("/api/v1/rooms", json={"name": "Java Developers"})

        resp = await auth_client.get("/api/v1/rooms", params={"search": "Python"})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any("Python" in r["name"] for r in items)


@pytest.mark.asyncio
class TestRoomAccess:
    """Room access control tests."""

    async def test_create_private_room(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.post("/api/v1/rooms", json={
            "name": "Private Room",
            "is_private": True,
        })
        assert resp.status_code == 201
        assert resp.json()["is_private"] is True

    async def test_get_members(self, auth_client: AsyncClient) -> None:
        create_resp = await auth_client.post("/api/v1/rooms", json={"name": "Members Room"})
        room_id = create_resp.json()["id"]

        resp = await auth_client.get(f"/api/v1/rooms/{room_id}/members")
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) == 1
        assert members[0]["role"] == "creator"

    async def test_room_not_found(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/rooms/99999")
        assert resp.status_code == 404
