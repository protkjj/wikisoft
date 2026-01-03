"""
WIKISOFT 4.1 n8n Integration

Native integration with n8n workflow automation.
Supports both webhook triggers and n8n API calls.
"""

from .adapter import (
    N8nConfig,
    N8nAdapter,
    N8nTriggerPayload,
    N8nWorkflowResult,
)

__all__ = [
    "N8nConfig",
    "N8nAdapter",
    "N8nTriggerPayload",
    "N8nWorkflowResult",
]
