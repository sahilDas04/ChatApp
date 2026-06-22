"""Aggregate API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.messages import router as messages_router
from app.api.v1.files import router as files_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(rooms_router)
api_router.include_router(messages_router)
api_router.include_router(files_router)
