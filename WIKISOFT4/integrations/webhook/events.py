"""
CloudEvents Implementation

Standard event format for interoperability with n8n, Temporal, and other platforms.
Spec: https://cloudevents.io/
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Standard event types for WIKISOFT4."""

    # Validation Events
    VALIDATION_STARTED = "com.wikisoft.validation.started"
    VALIDATION_COMPLETED = "com.wikisoft.validation.completed"
    VALIDATION_FAILED = "com.wikisoft.validation.failed"

    # Data Events
    DATA_UPLOADED = "com.wikisoft.data.uploaded"
    DATA_PROCESSED = "com.wikisoft.data.processed"
    DATA_EXPORTED = "com.wikisoft.data.exported"

    # Privacy Events
    PII_DETECTED = "com.wikisoft.privacy.pii_detected"
    DATA_MASKED = "com.wikisoft.privacy.data_masked"
    DATA_ANONYMIZED = "com.wikisoft.privacy.data_anonymized"

    # Workflow Events
    WORKFLOW_TRIGGERED = "com.wikisoft.workflow.triggered"
    WORKFLOW_COMPLETED = "com.wikisoft.workflow.completed"
    WORKFLOW_FAILED = "com.wikisoft.workflow.failed"

    # User Events
    USER_ACTION = "com.wikisoft.user.action"
    APPROVAL_REQUIRED = "com.wikisoft.approval.required"
    APPROVAL_GRANTED = "com.wikisoft.approval.granted"
    APPROVAL_DENIED = "com.wikisoft.approval.denied"


class CloudEvent(BaseModel):
    """
    CloudEvents v1.0 specification implementation.

    This is the standard format for events that can be consumed by
    n8n, Temporal, AWS EventBridge, Azure Event Grid, etc.
    """

    # Required fields
    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = "/wikisoft4"
    type: str

    # Optional fields
    datacontenttype: str = "application/json"
    dataschema: str | None = None
    subject: str | None = None
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Data payload
    data: dict[str, Any] = Field(default_factory=dict)

    # Extension attributes (WIKISOFT-specific)
    wikisoft_version: str = "4.1.0"
    wikisoft_environment: str = "production"
    wikisoft_correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "specversion": self.specversion,
            "id": self.id,
            "source": self.source,
            "type": self.type,
            "datacontenttype": self.datacontenttype,
            "time": self.time.isoformat(),
            "data": self.data,
        }

        # Add optional fields if present
        if self.dataschema:
            result["dataschema"] = self.dataschema
        if self.subject:
            result["subject"] = self.subject
        if self.wikisoft_correlation_id:
            result["wikisoftcorrelationid"] = self.wikisoft_correlation_id

        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)


def create_event(
    event_type: EventType,
    data: dict[str, Any],
    source: str = "/wikisoft4",
    subject: str | None = None,
    correlation_id: str | None = None,
) -> CloudEvent:
    """
    Create a CloudEvent with standard WIKISOFT4 settings.

    Args:
        event_type: Type of event
        data: Event payload
        source: Event source (default: /wikisoft4)
        subject: Optional subject (e.g., file ID, user ID)
        correlation_id: Optional correlation ID for tracing

    Returns:
        CloudEvent instance
    """
    return CloudEvent(
        type=event_type.value,
        source=source,
        subject=subject,
        data=data,
        wikisoft_correlation_id=correlation_id,
    )


# Convenience functions for common events
def validation_started_event(
    file_id: str,
    filename: str,
    user_id: str,
    correlation_id: str | None = None,
) -> CloudEvent:
    """Create a validation started event."""
    return create_event(
        EventType.VALIDATION_STARTED,
        data={
            "file_id": file_id,
            "filename": filename,
            "user_id": user_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
        subject=file_id,
        correlation_id=correlation_id,
    )


def validation_completed_event(
    file_id: str,
    filename: str,
    user_id: str,
    errors: int,
    warnings: int,
    duration_ms: int,
    correlation_id: str | None = None,
) -> CloudEvent:
    """Create a validation completed event."""
    return create_event(
        EventType.VALIDATION_COMPLETED,
        data={
            "file_id": file_id,
            "filename": filename,
            "user_id": user_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": {
                "errors": errors,
                "warnings": warnings,
                "duration_ms": duration_ms,
                "status": "error" if errors > 0 else "warning" if warnings > 0 else "success",
            },
        },
        subject=file_id,
        correlation_id=correlation_id,
    )


def pii_detected_event(
    file_id: str,
    pii_types: list[str],
    field_count: int,
    correlation_id: str | None = None,
) -> CloudEvent:
    """Create a PII detected event."""
    return create_event(
        EventType.PII_DETECTED,
        data={
            "file_id": file_id,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "pii_types": pii_types,
            "affected_fields": field_count,
            "action_required": True,
        },
        subject=file_id,
        correlation_id=correlation_id,
    )


def approval_required_event(
    request_id: str,
    request_type: str,
    requester_id: str,
    details: dict[str, Any],
    correlation_id: str | None = None,
) -> CloudEvent:
    """Create an approval required event."""
    return create_event(
        EventType.APPROVAL_REQUIRED,
        data={
            "request_id": request_id,
            "request_type": request_type,
            "requester_id": requester_id,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "details": details,
        },
        subject=request_id,
        correlation_id=correlation_id,
    )
