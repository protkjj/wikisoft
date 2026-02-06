"""
WIKISOFT 4.1 API

Security-first, privacy-focused API with workflow integration.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import health, validation, privacy, webhook, compat, auth, learn, windmill, ifrs, report, admin, agent
from .routes import auto_validate, diagnostic_questions, export
from .middleware.auth import AuthMiddleware
from .middleware.audit import AuditMiddleware
from .middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 OneCheck Starting...")
    print("🔒 Security: Enabled")
    print("🔐 Privacy: Enabled")
    print("🔄 Workflow: Enabled")

    # DB 초기화
    from core.database import init_db, migrate_json_to_sqlite, close_db
    print("💾 Database: Initializing...")
    init_db()
    migrate_json_to_sqlite()
    print("💾 Database: Ready")

    yield
    # Shutdown
    close_db()
    print("👋 OneCheck Shutting down...")


app = FastAPI(
    title="OneCheck API",
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
# Execution order: Auth → RateLimit → Audit → Handler
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
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
app.include_router(auth.router, prefix="/api/v4", tags=["Authentication"])
app.include_router(validation.router, prefix="/api/v4", tags=["Validation"])
app.include_router(privacy.router, prefix="/api/v4", tags=["Privacy"])
app.include_router(webhook.router, prefix="/api/v4", tags=["Webhook"])

# WIKISOFT3 호환 라우터 (프론트엔드 /api/* 경로 지원)
app.include_router(compat.router, tags=["Compatibility"])

# WIKISOFT3에서 마이그레이션된 라우터
app.include_router(learn.router, prefix="/api/v4", tags=["Learning"])
app.include_router(windmill.router, prefix="/api/v4", tags=["Windmill"])

# IFRS 1019 퇴직급여 계산 라우터
app.include_router(ifrs.router, prefix="/api/v4", tags=["IFRS 1019"])

# 리포트 생성 라우터
app.include_router(report.router, prefix="/api/v4", tags=["Report"])

# 관리자 라우터
app.include_router(admin.router, prefix="/api/v4", tags=["Admin"])

# AI 에이전트 라우터
app.include_router(agent.router, tags=["Agent"])

# WIKISOFT3에서 마이그레이션된 라우터 (v4 경로로 병렬 제공)
app.include_router(auto_validate.router, tags=["Auto Validate"])
app.include_router(diagnostic_questions.router, tags=["Diagnostic"])
app.include_router(export.router, tags=["Export"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OneCheck",
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
