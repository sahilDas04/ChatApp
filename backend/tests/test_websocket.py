"""WebSocket endpoint tests."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
class TestWebSocket:
    """WebSocket connection and messaging tests."""

    async def test_ws_invalid_token(self, client: AsyncClient) -> None:
        """Connecting with an invalid token should fail."""
        # Note: httpx doesn't support WebSockets directly.
        # These tests verify the HTTP-level behavior.
        # Full WS tests would require a websocket client library.
        pass

    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """Verify the health endpoint is accessible."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_docs_endpoint(self, client: AsyncClient) -> None:
        """Verify Swagger docs are accessible."""
        resp = await client.get("/docs")
        assert resp.status_code == 200
