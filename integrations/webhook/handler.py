"""
Webhook Handler

Send events to external systems via webhooks.
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from .events import CloudEvent


class WebhookConfig(BaseModel):
    """Webhook endpoint configuration."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    url: str
    secret: str | None = None  # For HMAC signature
    headers: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    retry_count: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000

    # Event filtering
    event_types: list[str] | None = None  # None = all events


class WebhookDelivery(BaseModel):
    """Record of a webhook delivery attempt."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    webhook_id: str
    event_id: str
    event_type: str
    url: str
    status: str  # pending, success, failed
    status_code: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    attempts: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class WebhookHandler:
    """
    Manages webhook deliveries with retry logic.
    """

    def __init__(self, configs: list[WebhookConfig] | None = None):
        self.configs: dict[str, WebhookConfig] = {}
        self.deliveries: list[WebhookDelivery] = []

        if configs:
            for config in configs:
                self.register(config)

    def register(self, config: WebhookConfig) -> None:
        """Register a webhook endpoint."""
        self.configs[config.id] = config

    def unregister(self, webhook_id: str) -> None:
        """Unregister a webhook endpoint."""
        self.configs.pop(webhook_id, None)

    def get_applicable_webhooks(self, event_type: str) -> list[WebhookConfig]:
        """Get webhooks that should receive an event type."""
        applicable = []
        for config in self.configs.values():
            if not config.enabled:
                continue
            if config.event_types is None or event_type in config.event_types:
                applicable.append(config)
        return applicable

    async def send_event(self, event: CloudEvent) -> list[WebhookDelivery]:
        """
        Send an event to all applicable webhooks.

        Args:
            event: CloudEvent to send

        Returns:
            List of delivery records
        """
        webhooks = self.get_applicable_webhooks(event.type)

        if not webhooks:
            return []

        # Send to all webhooks concurrently
        tasks = [
            self._deliver(config, event)
            for config in webhooks
        ]

        deliveries = await asyncio.gather(*tasks)
        self.deliveries.extend(deliveries)

        return list(deliveries)

    async def _deliver(
        self,
        config: WebhookConfig,
        event: CloudEvent,
    ) -> WebhookDelivery:
        """Deliver event to a single webhook with retries."""
        delivery = WebhookDelivery(
            webhook_id=config.id,
            event_id=event.id,
            event_type=event.type,
            url=config.url,
            status="pending",
        )

        payload = event.to_json()
        headers = {
            "Content-Type": "application/json",
            "X-CloudEvents-SpecVersion": "1.0",
            "X-WIKISOFT-Event-ID": event.id,
            "X-WIKISOFT-Event-Type": event.type,
            **config.headers,
        }

        # Add HMAC signature if secret is configured
        if config.secret:
            signature = self._create_signature(payload, config.secret)
            headers["X-WIKISOFT-Signature"] = signature

        async with httpx.AsyncClient(timeout=config.timeout_ms / 1000) as client:
            for attempt in range(config.retry_count):
                delivery.attempts = attempt + 1

                try:
                    response = await client.post(
                        config.url,
                        content=payload,
                        headers=headers,
                    )

                    delivery.status_code = response.status_code
                    delivery.response_body = response.text[:1000]  # Limit response size

                    if 200 <= response.status_code < 300:
                        delivery.status = "success"
                        delivery.completed_at = datetime.now(timezone.utc)
                        return delivery

                    # Retry on server errors
                    if response.status_code >= 500:
                        await asyncio.sleep(config.retry_delay_ms / 1000)
                        continue

                    # Don't retry on client errors
                    delivery.status = "failed"
                    delivery.error_message = f"HTTP {response.status_code}"
                    delivery.completed_at = datetime.now(timezone.utc)
                    return delivery

                except Exception as e:
                    delivery.error_message = str(e)
                    if attempt < config.retry_count - 1:
                        await asyncio.sleep(config.retry_delay_ms / 1000)
                        continue

        delivery.status = "failed"
        delivery.completed_at = datetime.now(timezone.utc)
        return delivery

    def _create_signature(self, payload: str, secret: str) -> str:
        """Create HMAC-SHA256 signature for payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def get_delivery_history(
        self,
        webhook_id: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """Get webhook delivery history with filters."""
        results = self.deliveries.copy()

        if webhook_id:
            results = [d for d in results if d.webhook_id == webhook_id]
        if event_type:
            results = [d for d in results if d.event_type == event_type]
        if status:
            results = [d for d in results if d.status == status]

        # Sort by creation time descending
        results.sort(key=lambda d: d.created_at, reverse=True)

        return results[:limit]


# Convenience function for simple webhook sending
async def send_webhook(
    url: str,
    event: CloudEvent,
    secret: str | None = None,
    headers: dict[str, str] | None = None,
    timeout_ms: int = 30000,
) -> WebhookDelivery:
    """
    Send a single webhook event.

    Args:
        url: Webhook URL
        event: CloudEvent to send
        secret: Optional HMAC secret for signing
        headers: Optional additional headers
        timeout_ms: Request timeout in milliseconds

    Returns:
        Delivery record
    """
    config = WebhookConfig(
        name="single",
        url=url,
        secret=secret,
        headers=headers or {},
        timeout_ms=timeout_ms,
        retry_count=1,
    )

    handler = WebhookHandler([config])
    deliveries = await handler.send_event(event)
    return deliveries[0] if deliveries else WebhookDelivery(
        webhook_id=config.id,
        event_id=event.id,
        event_type=event.type,
        url=url,
        status="failed",
        error_message="No applicable webhooks",
    )
