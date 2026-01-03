"""
Audit Logging Module

Comprehensive audit trail for all security-relevant actions.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from .config import security_settings


class AuditAction(str, Enum):
    """Auditable actions in the system."""

    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_PASSWORD_CHANGE = "auth.password_change"

    # Data Operations
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"

    # Validation
    VALIDATE_START = "validate.start"
    VALIDATE_COMPLETE = "validate.complete"
    VALIDATE_ERROR = "validate.error"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"

    # Workflow
    WORKFLOW_TRIGGER = "workflow.trigger"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_ERROR = "workflow.error"

    # Security Events
    SECURITY_PERMISSION_DENIED = "security.permission_denied"
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_SUSPICIOUS = "security.suspicious"

    # Privacy
    PRIVACY_PII_DETECTED = "privacy.pii_detected"
    PRIVACY_DATA_MASKED = "privacy.data_masked"
    PRIVACY_DATA_ANONYMIZED = "privacy.data_anonymized"


class AuditEntry(BaseModel):
    """Audit log entry."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: AuditAction
    user_id: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: str | None = None


# Configure structured logging
logger = structlog.get_logger("audit")

# In-memory audit store (replace with database in production)
_audit_store: list[AuditEntry] = []


def log_action(
    action: AuditAction,
    user_id: str | None = None,
    user_email: str | None = None,
    user_role: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict[str, Any] | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> AuditEntry:
    """
    Log an auditable action.

    Args:
        action: The action being performed
        user_id: ID of the user performing the action
        user_email: Email of the user (will be masked if audit_log_pii is False)
        user_role: Role of the user
        resource_type: Type of resource being accessed
        resource_id: ID of the resource
        ip_address: Client IP address
        user_agent: Client user agent
        details: Additional details (PII will be filtered)
        success: Whether the action succeeded
        error_message: Error message if action failed

    Returns:
        The created audit entry
    """
    # Mask PII if configured
    if not security_settings.audit_log_pii:
        if user_email:
            user_email = _mask_email(user_email)
        if details:
            details = _filter_pii_from_details(details)

    entry = AuditEntry(
        action=action,
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        success=success,
        error_message=error_message,
    )

    # Store entry
    _audit_store.append(entry)

    # Log to structured logger
    log_data = entry.model_dump()
    log_data["timestamp"] = entry.timestamp.isoformat()

    # Prepare log data without 'action' duplication
    filtered_log = {k: v for k, v in log_data.items() if v is not None and k != 'action'}

    if success:
        logger.info(
            "audit_event",
            action=action.value,
            **filtered_log
        )
    else:
        logger.warning(
            "audit_event_failed",
            action=action.value,
            **filtered_log
        )

    return entry


def get_audit_trail(
    user_id: str | None = None,
    action: AuditAction | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditEntry]:
    """
    Query audit trail with filters.

    Args:
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of matching audit entries
    """
    results = _audit_store.copy()

    # Apply filters
    if user_id:
        results = [e for e in results if e.user_id == user_id]
    if action:
        results = [e for e in results if e.action == action]
    if resource_type:
        results = [e for e in results if e.resource_type == resource_type]
    if resource_id:
        results = [e for e in results if e.resource_id == resource_id]
    if start_date:
        results = [e for e in results if e.timestamp >= start_date]
    if end_date:
        results = [e for e in results if e.timestamp <= end_date]

    # Sort by timestamp descending
    results.sort(key=lambda e: e.timestamp, reverse=True)

    # Apply pagination
    return results[offset:offset + limit]


def _mask_email(email: str) -> str:
    """Mask email for audit logging."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def _filter_pii_from_details(details: dict[str, Any]) -> dict[str, Any]:
    """Remove PII from audit details."""
    pii_fields = {
        "password", "token", "secret", "key", "ssn", "social_security",
        "credit_card", "phone", "email", "address", "birth_date",
        "주민번호", "전화번호", "이메일", "주소", "생년월일",
    }

    filtered = {}
    for key, value in details.items():
        key_lower = key.lower()
        if any(pii in key_lower for pii in pii_fields):
            filtered[key] = "[REDACTED]"
        elif isinstance(value, dict):
            filtered[key] = _filter_pii_from_details(value)
        else:
            filtered[key] = value

    return filtered
