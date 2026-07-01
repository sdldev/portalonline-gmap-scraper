"""Per-user rate limiting middleware (60 req/min authenticated, 10 req/min by IP for unauthenticated)."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        ip_max_requests: int = 10,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ip_max_requests = ip_max_requests
        self._buckets: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=max_requests + 10)
        )

    def _clean_bucket(self, user_id: str, now: float) -> None:
        bucket = self._buckets[user_id]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    async def check_rate(self, request: Request) -> None:
        user_id = getattr(request.state, "user_id", None)
        if getattr(request.state, "user_role", None) == "admin" and user_id:
            return

        now = time.monotonic()

        if user_id:
            bucket_key = user_id
            limit = self.max_requests
        else:
            client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not client_ip:
                client_ip = request.client.host if request.client else "unknown"
            bucket_key = f"ip:{client_ip}"
            limit = self.ip_max_requests

        self._clean_bucket(bucket_key, now)
        bucket = self._buckets[bucket_key]

        if len(bucket) >= limit:
            reset_at = int(bucket[0] + self.window_seconds)
            retry_after = max(1, reset_at - int(now))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(retry_after),
                },
            )

        bucket.append(now)


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Return the global RateLimiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
