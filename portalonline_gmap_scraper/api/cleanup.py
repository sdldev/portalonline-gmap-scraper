"""Scheduled data retention cleanup and vacuum."""

import asyncio
import logging
import os

import aiosqlite

from .store import run_cleanup

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """Background asyncio task that runs cleanup daily."""

    def __init__(
        self,
        db: aiosqlite.Connection,
        retention_days: int = 90,
        cleanup_hour: int = 3,
    ):
        self.db = db
        self.retention_days = retention_days
        self.cleanup_hour = cleanup_hour
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(3600)
            now_hour = __import__("datetime").datetime.now().hour
            if now_hour == self.cleanup_hour:
                try:
                    result = await run_cleanup(
                        self.db, older_than_days=self.retention_days
                    )
                    logger.info("Scheduled cleanup completed: %s", result)
                except Exception:
                    logger.exception("Scheduled cleanup failed")

    async def start(self) -> None:
        logger.info(
            "Cleanup scheduler started: retention=%dd, hour=%d",
            self.retention_days, self.cleanup_hour,
        )
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


def get_cleanup_scheduler(db: aiosqlite.Connection) -> CleanupScheduler:
    """Create a CleanupScheduler from env vars."""
    retention = int(os.getenv("DATA_RETENTION_DAYS", "90"))
    hour = int(os.getenv("AUTO_CLEANUP_HOUR", "3"))
    return CleanupScheduler(db, retention, hour)
