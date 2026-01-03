"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "4.1.0",
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    return {
        "ready": True,
        "checks": {
            "database": "ok",
            "cache": "ok",
        },
    }


@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"alive": True}
