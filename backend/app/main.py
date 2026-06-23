"""ChatShare — FastAPI Application Entry Point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ChatShareException

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("chatshare") 


# ── Rate Limiter ──────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    logger.info("🚀 ChatShare API starting up...")
    # Ensure upload directory exists
    settings.upload_path  # property call creates directory
    yield
    logger.info("🛑 ChatShare API shutting down...")


# ── App Factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ChatShare API",
        description="Production-ready File Sharing & Real-Time Chat API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for custom exceptions
    @app.exception_handler(ChatShareException)
    async def chatshare_exception_handler(
        request: Request, exc: ChatShareException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # Static files — serve uploads directory for avatars and room files
    import os
    uploads_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    # Routes
    app.include_router(api_router)

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "healthy", "service": "ChatShare API"}

    return app


app = create_app()
