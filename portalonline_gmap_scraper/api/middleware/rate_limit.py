"""Per-user rate limiting middleware (60 req/min, admin exempt)."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
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
        if not user_id:
            return

        if getattr(request.state, "user_role", None) == "admin":
            return

        now = time.monotonic()
        self._clean_bucket(user_id, now)
        bucket = self._buckets[user_id]

        if len(bucket) >= self.max_requests:
            reset_at = int(bucket[0] + self.window_seconds)
            retry_after = max(1, reset_at - int(now))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(retry_after),
                },
            )

        bucket.append(now)


_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
