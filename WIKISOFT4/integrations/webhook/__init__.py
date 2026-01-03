"""
WIKISOFT 4.1 Webhook Integration

Generic webhook support with CloudEvents format for maximum compatibility.
"""

from .events import (
    CloudEvent,
    create_event,
    EventType,
)
from .handler import (
    WebhookConfig,
    WebhookHandler,
    send_webhook,
)

__all__ = [
    "CloudEvent",
    "create_event",
    "EventType",
    "WebhookConfig",
    "WebhookHandler",
    "send_webhook",
]
