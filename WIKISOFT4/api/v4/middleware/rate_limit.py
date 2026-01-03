"""Rate Limiting Middleware."""

from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: DefaultDict[str, list[datetime]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        now = datetime.now(timezone.utc)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if (now - req_time).total_seconds() < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            from core.security import log_action, AuditAction
            log_action(
                action=AuditAction.SECURITY_RATE_LIMIT,
                ip_address=client_ip,
                details={"path": request.url.path},
                success=False,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute.",
                    "retry_after": 60,
                },
            )

        # Record this request
        self.requests[client_ip].append(now)

        return await call_next(request)
