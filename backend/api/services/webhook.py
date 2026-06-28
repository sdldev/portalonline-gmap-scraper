"""Webhook delivery service for job event notifications."""

import asyncio
import logging

import httpx

from api.models import WebhookConfig

logger = logging.getLogger(__name__)


class WebhookService:
    """Manages webhook delivery on job events."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def deliver(
        self,
        url: str,
        event: str,
        job_id: str,
        payload: dict,
    ) -> bool:
        """Send webhook with retry. Returns True on success, False on failure."""
        body = {
            "event": event,
            "job_id": job_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": payload,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        url, json=body,
                        headers={"Content-Type": "application/json"},
                    )
                    if resp.status_code < 500:
                        logger.debug(
                            "Webhook delivered: %s -> %s (attempt %d)",
                            event, url, attempt,
                        )
                        return True
            except Exception as e:
                logger.warning(
                    "Webhook attempt %d/%d failed: %s -> %s: %s",
                    attempt, self.max_retries, event, url, e,
                )

            if attempt < self.max_retries:
                await asyncio.sleep(2 ** attempt)

        logger.warning(
            "Webhook delivery failed after %d attempts: %s -> %s",
            self.max_retries, event, url,
        )
        return False

    async def notify_job_completed(
        self, webhook: WebhookConfig, job_id: str, summary: dict
    ) -> None:
        """Deliver job.completed event if configured."""
        if "job.completed" not in webhook.events:
            return
        await self.deliver(webhook.url, "job.completed", job_id, summary)

    async def notify_job_failed(
        self, webhook: WebhookConfig, job_id: str, error: str
    ) -> None:
        """Deliver job.failed event if configured."""
        if "job.failed" not in webhook.events:
            return
        await self.deliver(webhook.url, "job.failed", job_id, {"error": error})


_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    """Return the global WebhookService singleton."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
