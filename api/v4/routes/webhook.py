"""Webhook endpoints for workflow integration."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel

from integrations.webhook import CloudEvent, create_event, EventType
from integrations.n8n import N8nAdapter, N8nConfig, N8nTriggerPayload

router = APIRouter()


class WebhookTriggerRequest(BaseModel):
    """Incoming webhook trigger request."""
    workflow_id: str
    data: dict[str, Any] = {}
    callback_url: str | None = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    received: bool
    correlation_id: str
    message: str


@router.post("/webhook/n8n", response_model=WebhookResponse)
async def n8n_webhook(
    request: WebhookTriggerRequest,
    x_n8n_signature: str | None = Header(None),
):
    """
    Receive webhook trigger from n8n.

    This endpoint is called by n8n to trigger WIKISOFT4 actions.
    """
    from uuid import uuid4

    correlation_id = str(uuid4())

    # TODO: Verify signature if configured
    # TODO: Process the webhook based on workflow_id

    return WebhookResponse(
        received=True,
        correlation_id=correlation_id,
        message=f"Webhook received for workflow: {request.workflow_id}",
    )


@router.post("/webhook/generic")
async def generic_webhook(request: Request):
    """
    Receive generic webhook in CloudEvents format.

    Supports any CloudEvents-compatible source.
    """
    body = await request.json()

    # Validate CloudEvents format
    if "specversion" not in body or "type" not in body:
        raise HTTPException(
            status_code=400,
            detail="Invalid CloudEvents format: missing required fields",
        )

    event_type = body.get("type")
    event_data = body.get("data", {})

    # Log the event
    from core.security import log_action, AuditAction
    log_action(
        action=AuditAction.WORKFLOW_TRIGGER,
        details={
            "event_type": event_type,
            "source": body.get("source"),
        },
    )

    return {
        "received": True,
        "event_id": body.get("id"),
        "event_type": event_type,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/webhook/test")
async def test_webhook(url: str, event_type: str = "test"):
    """
    Send a test webhook to verify connectivity.
    """
    from integrations.webhook import send_webhook

    test_event = create_event(
        EventType.USER_ACTION,
        data={
            "type": "test",
            "message": "This is a test webhook from WIKISOFT4",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    delivery = await send_webhook(url, test_event)

    return {
        "sent": delivery.status == "success",
        "status": delivery.status,
        "status_code": delivery.status_code,
        "error": delivery.error_message,
    }


@router.get("/webhook/events")
async def list_event_types():
    """List all available event types for webhooks."""
    return {
        "event_types": [
            {
                "type": event_type.value,
                "name": event_type.name,
                "category": event_type.value.split(".")[2],
            }
            for event_type in EventType
        ]
    }
