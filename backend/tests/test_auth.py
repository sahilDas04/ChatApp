"""Authentication API tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    """Registration endpoint tests."""

    async def test_register_success(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "Strong1Pass",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "username": "another",
            "email": "test@example.com",
            "password": "Strong1Pass",
        })
        assert resp.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "nodigits",
        })
        assert resp.status_code == 422

    async def test_register_short_username(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "username": "ab",
            "email": "short@example.com",
            "password": "Strong1Pass",
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Login endpoint tests."""

    async def test_login_success(self, client: AsyncClient, test_user) -> None:
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user) -> None:
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPass1",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Test1234",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestProtectedEndpoints:
    """Protected endpoint access tests."""

    async def test_get_me_authenticated(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_get_me_no_token(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 422  # Missing header

    async def test_get_me_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestTokenRefresh:
    """Token refresh tests."""

    async def test_refresh_success(self, client: AsyncClient, test_user) -> None:
        # Login first
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234",
        })
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token(self, client: AsyncClient, test_user) -> None:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234",
        })
        access_token = login_resp.json()["access_token"]

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert resp.status_code == 401
