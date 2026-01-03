"""
n8n Workflow Adapter

Integrates WIKISOFT4 with n8n workflow automation platform.
Supports:
- Webhook triggers (n8n → WIKISOFT4)
- Workflow execution (WIKISOFT4 → n8n)
- Callback handling (n8n → WIKISOFT4)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from ..webhook.events import CloudEvent, EventType, create_event


class N8nConfig(BaseModel):
    """n8n connection configuration."""

    base_url: str  # e.g., "https://n8n.example.com"
    api_key: str | None = None
    webhook_secret: str | None = None
    default_timeout_ms: int = 30000


class N8nTriggerPayload(BaseModel):
    """Payload received from n8n webhook trigger."""

    workflow_id: str
    execution_id: str | None = None
    trigger_type: str = "webhook"
    data: dict[str, Any] = Field(default_factory=dict)
    callback_url: str | None = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))


class N8nWorkflowResult(BaseModel):
    """Result of n8n workflow execution."""

    execution_id: str
    workflow_id: str
    status: str  # running, success, failed, waiting
    started_at: datetime
    finished_at: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class N8nAdapter:
    """
    Adapter for n8n workflow automation.

    Usage:
        adapter = N8nAdapter(N8nConfig(
            base_url="https://n8n.example.com",
            api_key="your-api-key",
        ))

        # Execute a workflow
        result = await adapter.execute_workflow(
            workflow_id="validation-workflow",
            data={"file_id": "123", "user_id": "456"},
        )

        # Handle callback from n8n
        await adapter.handle_callback(payload)
    """

    def __init__(self, config: N8nConfig):
        self.config = config
        self._pending_executions: dict[str, N8nTriggerPayload] = {}

    async def execute_workflow(
        self,
        workflow_id: str,
        data: dict[str, Any],
        wait_for_completion: bool = False,
        callback_url: str | None = None,
    ) -> N8nWorkflowResult:
        """
        Execute an n8n workflow.

        Args:
            workflow_id: ID or name of the workflow
            data: Input data for the workflow
            wait_for_completion: If True, wait for workflow to complete
            callback_url: URL for n8n to call when workflow completes

        Returns:
            Workflow execution result
        """
        execution_id = str(uuid4())
        started_at = datetime.now(timezone.utc)

        # Build webhook URL
        webhook_url = f"{self.config.base_url}/webhook/{workflow_id}"

        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["X-N8N-API-KEY"] = self.config.api_key

        payload = {
            "execution_id": execution_id,
            "source": "wikisoft4",
            "data": data,
        }

        if callback_url:
            payload["callback_url"] = callback_url

        async with httpx.AsyncClient(timeout=self.config.default_timeout_ms / 1000) as client:
            try:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                )

                if response.status_code >= 400:
                    return N8nWorkflowResult(
                        execution_id=execution_id,
                        workflow_id=workflow_id,
                        status="failed",
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                # Parse response
                result_data = response.json() if response.text else {}

                return N8nWorkflowResult(
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    status="success" if not wait_for_completion else "running",
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc) if not wait_for_completion else None,
                    data=result_data,
                )

            except Exception as e:
                return N8nWorkflowResult(
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                    status="failed",
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                    error=str(e),
                )

    def parse_trigger_payload(self, raw_payload: dict[str, Any]) -> N8nTriggerPayload:
        """
        Parse incoming webhook payload from n8n.

        Args:
            raw_payload: Raw JSON payload from n8n

        Returns:
            Parsed trigger payload
        """
        return N8nTriggerPayload(
            workflow_id=raw_payload.get("workflow_id", "unknown"),
            execution_id=raw_payload.get("execution_id"),
            trigger_type=raw_payload.get("trigger_type", "webhook"),
            data=raw_payload.get("data", {}),
            callback_url=raw_payload.get("callback_url"),
            correlation_id=raw_payload.get("correlation_id", str(uuid4())),
        )

    async def send_callback(
        self,
        callback_url: str,
        success: bool,
        data: dict[str, Any],
        error: str | None = None,
    ) -> bool:
        """
        Send callback to n8n workflow.

        Args:
            callback_url: URL to send callback to
            success: Whether the operation succeeded
            data: Result data
            error: Error message if failed

        Returns:
            True if callback was sent successfully
        """
        payload = {
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        if error:
            payload["error"] = error

        headers = {"Content-Type": "application/json"}
        if self.config.webhook_secret:
            # Add signature header
            import hashlib
            import hmac
            import json
            payload_str = json.dumps(payload)
            signature = hmac.new(
                self.config.webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-WIKISOFT-Signature"] = f"sha256={signature}"

        async with httpx.AsyncClient(timeout=self.config.default_timeout_ms / 1000) as client:
            try:
                response = await client.post(
                    callback_url,
                    json=payload,
                    headers=headers,
                )
                return 200 <= response.status_code < 300
            except Exception:
                return False

    def create_completion_event(
        self,
        trigger: N8nTriggerPayload,
        success: bool,
        result_data: dict[str, Any],
        error: str | None = None,
    ) -> CloudEvent:
        """
        Create a CloudEvent for workflow completion.

        Args:
            trigger: Original trigger payload
            success: Whether workflow succeeded
            result_data: Result data
            error: Error message if failed

        Returns:
            CloudEvent for the completion
        """
        event_type = EventType.WORKFLOW_COMPLETED if success else EventType.WORKFLOW_FAILED

        return create_event(
            event_type,
            data={
                "workflow_id": trigger.workflow_id,
                "execution_id": trigger.execution_id,
                "trigger_type": trigger.trigger_type,
                "success": success,
                "result": result_data,
                "error": error,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            subject=trigger.workflow_id,
            correlation_id=trigger.correlation_id,
        )


# Pre-defined workflow templates
class WorkflowTemplates:
    """Common n8n workflow patterns for WIKISOFT4."""

    @staticmethod
    def validation_approval_workflow() -> dict[str, Any]:
        """
        Workflow: Validation → Approval → Notification

        This workflow template can be imported into n8n.
        """
        return {
            "name": "WIKISOFT4 Validation Approval",
            "nodes": [
                {
                    "name": "Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {
                        "path": "wikisoft4-validation",
                        "httpMethod": "POST",
                    },
                },
                {
                    "name": "Check Errors",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "number": [{
                                "value1": "={{$json.data.errors}}",
                                "operation": "larger",
                                "value2": 0,
                            }],
                        },
                    },
                },
                {
                    "name": "Request Approval",
                    "type": "n8n-nodes-base.slack",
                    "parameters": {
                        "channel": "#approvals",
                        "text": "Validation completed with errors. Please review.",
                    },
                },
                {
                    "name": "Auto Approve",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "url": "={{$json.callback_url}}",
                        "method": "POST",
                        "body": {"approved": True},
                    },
                },
            ],
        }

    @staticmethod
    def pii_alert_workflow() -> dict[str, Any]:
        """
        Workflow: PII Detection → Alert → Log

        This workflow template can be imported into n8n.
        """
        return {
            "name": "WIKISOFT4 PII Alert",
            "nodes": [
                {
                    "name": "Webhook Trigger",
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {
                        "path": "wikisoft4-pii-alert",
                        "httpMethod": "POST",
                    },
                },
                {
                    "name": "Send Alert",
                    "type": "n8n-nodes-base.emailSend",
                    "parameters": {
                        "toEmail": "security@company.com",
                        "subject": "PII Detected in Upload",
                        "text": "PII was detected: {{$json.data.pii_types}}",
                    },
                },
                {
                    "name": "Log to Database",
                    "type": "n8n-nodes-base.postgres",
                    "parameters": {
                        "operation": "insert",
                        "table": "security_logs",
                    },
                },
            ],
        }
