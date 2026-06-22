"""Authentication dependencies for FastAPI."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token, is_token_blacklisted
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the JWT from the Authorization header.

    Returns the authenticated User object.

    Raises:
        AuthenticationError: If the token is missing, invalid, blacklisted, or the user is inactive.
    """
    if not authorization.startswith("Bearer "):
        raise AuthenticationError(detail="Authorization header must start with 'Bearer'")

    token = authorization[7:]  # Strip "Bearer "

    if is_token_blacklisted(token):
        raise AuthenticationError(detail="Token has been revoked")

    payload = decode_token(token, expected_type="access")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError(detail="Invalid token payload")

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id_str))

    if not user:
        raise AuthenticationError(detail="User not found")
    if not user.is_active:
        raise AuthenticationError(detail="Account is deactivated")

    return user
