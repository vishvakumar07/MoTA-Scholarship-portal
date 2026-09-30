"""
In-memory Sliding Window Rate Limiter for Phase 8.

Protects sensitive endpoints:
- Authentication (login, registration)
- Expensive AI/OCR processing triggers
- Document uploads
- Data exports
- Government verification calls
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """
    Sliding window in-memory rate limiter.
    Stores timestamps of requests per bucket key.
    """

    def __init__(self, requests_limit: int, window_seconds: int, bucket_name: str = "default"):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.bucket_name = bucket_name
        self._store: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str) -> tuple[bool, int]:
        """
        Check if the key has exceeded rate limit.
        Returns:
            (is_limited: bool, retry_after_seconds: int)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Prune older entries
        self._store[key] = [t for t in self._store[key] if t > window_start]

        if len(self._store[key]) >= self.requests_limit:
            oldest_in_window = self._store[key][0]
            retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
            return True, retry_after

        # Record this request
        self._store[key].append(now)
        return False, 0

    def reset(self, key: Optional[str] = None):
        """Reset the rate limit store (useful in tests)."""
        if key:
            self._store.pop(key, None)
        else:
            self._store.clear()


# Pre-configured rate limiters
# Login: 10 requests per minute per IP / identifier
login_rate_limiter = SlidingWindowRateLimiter(requests_limit=10, window_seconds=60, bucket_name="login")

# Registration: 5 requests per minute per IP
register_rate_limiter = SlidingWindowRateLimiter(requests_limit=5, window_seconds=60, bucket_name="register")

# Processing / AI Trigger: 10 requests per minute per user
processing_rate_limiter = SlidingWindowRateLimiter(requests_limit=10, window_seconds=60, bucket_name="processing")

# Exports: 5 requests per minute per user
export_rate_limiter = SlidingWindowRateLimiter(requests_limit=5, window_seconds=60, bucket_name="export")


def enforce_rate_limit(
    limiter: SlidingWindowRateLimiter,
    key_func: Optional[Callable[[Request], str]] = None,
):
    """
    FastAPI dependency to enforce rate limiting.
    """
    async def dependency(request: Request):
        if key_func:
            key = key_func(request)
        else:
            # Default to client host IP
            key = request.client.host if request.client else "unknown"

        is_limited, retry_after = limiter.is_rate_limited(key)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests for {limiter.bucket_name}. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
    return dependency
