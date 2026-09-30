"""Common Pydantic v2 schemas and response wrappers."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard unified API response wrapper."""
    success: bool = True
    message: str | None = None
    data: T | None = None
    error: dict[str, Any] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated collection response."""
    items: list[T]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total_pages: int


class HealthStatus(BaseModel):
    """Health check payload."""
    status: str
    environment: str
    database: bool
    redis: bool
    ai_available: bool
    ocr_available: bool
    timestamp: str
