"""Webhook delivery service for job event notifications."""

import asyncio
import hashlib
import hmac
import ipaddress
import logging
import os
from urllib.parse import urlparse

import httpx

from api.models import WebhookConfig

logger = logging.getLogger(__name__)

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fd00:ec2::254/128"),
)


def validate_webhook_url(url: str) -> None:
    """Validate webhook URL against SSRF. Raises ValueError on invalid URL."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Webhook URL must use http or https scheme")
    if parsed.scheme == "http" and not os.getenv("WEBHOOK_ALLOW_HTTP", "").lower() in ("1", "true", "yes"):
        raise ValueError("Webhook URL must use https scheme")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Webhook URL missing hostname")
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise ValueError(f"Webhook URL resolves to private IP: {hostname}")
    except ValueError as e:
        if "private IP" in str(e) or "must use" in str(e):
            raise
        # hostname is a domain name, not an IP — allow it
        pass


class WebhookService:
    """Manages webhook delivery on job events."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._webhook_secret = os.getenv("WEBHOOK_SECRET", "")

    async def deliver(
        self,
        url: str,
        event: str,
        job_id: str,
        payload: dict,
        webhook_secret: str | None = None,
    ) -> bool:
        """Send webhook with retry. Returns True on success, False on failure."""
        validate_webhook_url(url)
        body = {
            "event": event,
            "job_id": job_id,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": payload,
        }

        headers = {"Content-Type": "application/json"}
        if webhook_secret:
            import json
            body_bytes = json.dumps(body, separators=(",", ":")).encode()
            sig = hmac.new(webhook_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={sig}"

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        url, json=body, headers=headers,
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
        self, webhook: WebhookConfig, job_id: str, summary: dict, webhook_secret: str | None = None
    ) -> None:
        """Deliver job.completed event if configured."""
        if "job.completed" not in webhook.events:
            return
        await self.deliver(webhook.url, "job.completed", job_id, summary, webhook_secret=webhook_secret)

    async def notify_job_failed(
        self, webhook: WebhookConfig, job_id: str, error: str, webhook_secret: str | None = None
    ) -> None:
        """Deliver job.failed event if configured."""
        if "job.failed" not in webhook.events:
            return
        await self.deliver(webhook.url, "job.failed", job_id, {"error": error}, webhook_secret=webhook_secret)


_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    """Return the global WebhookService singleton."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
