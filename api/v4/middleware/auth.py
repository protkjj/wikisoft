"""Authentication Middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT and API Key authentication middleware."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/api/v4/docs",
        "/api/v4/redoc",
        "/api/v4/openapi.json",
        "/api/v4/health",
        "/api/v4/health/ready",
        "/api/v4/health/live",
    }

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")

        if not auth_header and not api_key:
            # For now, allow unauthenticated access in development
            # In production, return 401
            pass

        # TODO: Implement actual authentication
        # - Verify JWT token
        # - Verify API key
        # - Set user in request state

        response = await call_next(request)
        return response
