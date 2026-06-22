"""Authentication service — business logic for auth flows."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserRegister


class AuthService:
    """Handles registration, login, token refresh, and logout."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def register(self, data: UserRegister) -> User:
        """Register a new user."""
        # Check for duplicate email
        if await self.repo.get_by_email(data.email):
            raise ConflictError(detail="Email already registered")

        # Check for duplicate username
        if await self.repo.get_by_username(data.username):
            raise ConflictError(detail="Username already taken")

        hashed = hash_password(data.password)
        user = await self.repo.create(
            username=data.username,
            email=data.email,
            password_hash=hashed,
        )
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate and return token pair."""
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError(detail="Invalid email or password")

        if not user.is_active:
            raise AuthenticationError(detail="Account is deactivated")

        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Issue a new access token using a refresh token."""
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError(detail="Invalid token payload")

        user = await self.repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise AuthenticationError(detail="User not found or deactivated")

        new_access = create_access_token(data={"sub": str(user.id)})
        new_refresh = create_refresh_token(data={"sub": str(user.id)})

        # Blacklist old refresh token
        blacklist_token(refresh_token)

        return TokenResponse(access_token=new_access, refresh_token=new_refresh)

    @staticmethod
    def logout(access_token: str) -> None:
        """Blacklist the current access token."""
        blacklist_token(access_token)
