"""Shared FastAPI dependencies."""

from fastapi import Request


async def get_db(request: Request):
    """Dependency returning the aiosqlite connection from app state."""
    return request.app.state.db


def get_job_manager(request: Request):
    """Dependency returning the JobManager from app state."""
    return request.app.state.job_manager


def get_rate_limiter():
    """Dependency returning the global RateLimiter singleton."""
    from api.middleware.rate_limit import get_rate_limiter as _grl
    return _grl()
