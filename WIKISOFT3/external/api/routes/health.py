from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health() -> dict:
    return {"status": "ok", "version": "v3-draft"}
