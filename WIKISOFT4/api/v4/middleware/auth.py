"""Authentication Middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.security.auth import verify_token, User


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
        # Auth endpoints (login, register don't need auth)
        "/api/v4/auth/login",
        "/api/v4/auth/register",
        "/api/v4/auth/verify",
        # WIKISOFT3 compatibility paths
        "/api/health",
        "/api/diagnostic-questions",
        "/api/auto-validate",
        "/api/windmill/latest",
        "/api/export/errors",
        "/api/export/xlsx",
    }

    # Paths that require authentication (strict mode)
    PROTECTED_PATHS = {
        "/api/v4/auth/me",
        "/api/v4/auth/logout",
        "/api/v4/auth/refresh",
        "/api/v4/auth/users",
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public paths
        if path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")

        user = None

        # Verify JWT token
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            token_data = verify_token(token)
            if token_data:
                # Store user info in request state
                request.state.user_id = token_data.sub
                request.state.scopes = token_data.scopes
                user = token_data

        # Verify API Key (simplified - in production, check against database)
        elif api_key and api_key.startswith("wk4_"):
            # API key is valid format, allow access
            request.state.api_key = api_key
            request.state.user_id = "api_user"
            user = True

        # Check if path requires authentication
        if path in self.PROTECTED_PATHS and not user:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "인증이 필요합니다",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # For other paths, allow access but mark as unauthenticated
        if not user:
            request.state.user_id = None
            request.state.scopes = []

        response = await call_next(request)
        return response
