"""Custom exception classes for the application."""

from __future__ import annotations


class ChatShareException(Exception):
    """Base exception for the ChatShare application."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class AuthenticationError(ChatShareException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(detail=detail, status_code=401)


class AuthorizationError(ChatShareException):
    """Raised when a user lacks permission."""

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(detail=detail, status_code=403)


class NotFoundError(ChatShareException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(detail=f"{resource} not found", status_code=404)


class ConflictError(ChatShareException):
    """Raised when a resource already exists."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(detail=detail, status_code=409)


class FileSizeError(ChatShareException):
    """Raised when a file exceeds the maximum size."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(
            detail=f"File exceeds maximum size of {max_mb}MB",
            status_code=413,
        )


class FileTypeError(ChatShareException):
    """Raised when a file type is not allowed."""

    def __init__(self, allowed: list[str]) -> None:
        super().__init__(
            detail=f"File type not allowed. Allowed: {', '.join(allowed)}",
            status_code=415,
        )


class RateLimitError(ChatShareException):
    """Raised when rate limit is exceeded."""

    def __init__(self) -> None:
        super().__init__(detail="Rate limit exceeded. Try again later.", status_code=429)
