"""
WIKISOFT 4.1 API

Security-first, privacy-focused API with workflow integration.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import health, validation, privacy, webhook
from .middleware.auth import AuthMiddleware
from .middleware.audit import AuditMiddleware
from .middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 WIKISOFT 4.1 Starting...")
    print("🔒 Security: Enabled")
    print("🔐 Privacy: Enabled")
    print("🔄 Workflow: Enabled")
    yield
    # Shutdown
    print("👋 WIKISOFT 4.1 Shutting down...")


app = FastAPI(
    title="WIKISOFT 4.1 API",
    description="Security-first, privacy-focused HR/Finance data validation platform",
    version="4.1.0",
    docs_url="/api/v4/docs",
    redoc_url="/api/v4/redoc",
    openapi_url="/api/v4/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - last added = first executed)
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v4", tags=["Health"])
app.include_router(validation.router, prefix="/api/v4", tags=["Validation"])
app.include_router(privacy.router, prefix="/api/v4", tags=["Privacy"])
app.include_router(webhook.router, prefix="/api/v4", tags=["Webhook"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "WIKISOFT",
        "version": "4.1.0",
        "status": "running",
        "features": {
            "security": True,
            "privacy": True,
            "workflow": True,
        },
        "api": {
            "version": "v4",
            "docs": "/api/v4/docs",
        },
    }
