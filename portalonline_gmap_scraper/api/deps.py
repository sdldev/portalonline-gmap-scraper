"""Shared FastAPI dependencies."""

from fastapi import Request


async def get_db(request: Request):
    return request.app.state.db


def get_job_manager(request: Request):
    return request.app.state.job_manager


def get_rate_limiter():
    from .middleware.rate_limit import get_rate_limiter as _grl
    return _grl()
