"""Async database session management."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Render free tier: keep pool small (Postgres allows max 25 concurrent connections)
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,   # Recycle connections after 30 min to avoid idle timeout drops
    pool_pre_ping=True,  # Verify connection health before using (critical after Render sleep)
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
