from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from internal.queue.jobs import enqueue_jobs, get_job, update_job

router = APIRouter(prefix="/api/batch-validate", tags=["batch-validate"])


@router.post("")
async def batch_validate(files: List[UploadFile] = File(...)) -> dict:
    """배치 파일 검증 (현재 미구현 - 단일 파일 검증 사용 권장)

    NOTE: 이 엔드포인트는 아직 완전히 구현되지 않았습니다.
    실제 파일 처리가 되지 않으며, 단일 파일 검증(/api/auto-validate)을 사용해주세요.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="at least one file is required")

    # 기능 미구현 경고
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="배치 처리 기능은 현재 개발 중입니다. 단일 파일 검증(/api/auto-validate)을 사용해주세요."
    )


@router.get("/{job_id}")
async def batch_status(job_id: str) -> dict:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return {"job_id": job_id, **job}


@router.post("/{job_id}/webhook")
async def batch_webhook(job_id: str, payload: dict) -> dict:
    """워커가 상태/진행률을 푸시하는 웹훅 스텁."""
    status_val = payload.get("status", "running")
    progress = payload.get("progress", 0)
    result = payload.get("result")
    error = payload.get("error")
    update_job(job_id, status=status_val, progress=progress, result=result, error=error)
    return {"job_id": job_id, "status": status_val, "progress": progress}
