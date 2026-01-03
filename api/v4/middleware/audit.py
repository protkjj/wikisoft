"""Audit Logging Middleware."""

from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all API requests for audit trail."""

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)

        # Get request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Log the request (skip health checks)
        if not path.startswith("/api/v4/health"):
            from core.security import log_action, AuditAction

            log_action(
                action=AuditAction.DATA_READ,  # Generic action
                ip_address=client_ip,
                user_agent=user_agent,
                details={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
                success=response.status_code < 400,
            )

        return response
