from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from internal.queue.jobs import enqueue_jobs, get_job, update_job

router = APIRouter(prefix="/batch-validate", tags=["batch-validate"])


@router.post("")
async def batch_validate(files: List[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="at least one file is required")

    file_names = [f.filename or "unknown" for f in files]
    job_id = enqueue_jobs(file_names)

    # TODO: 실제 큐(RQ/Celery 등)에 enqueue, 워커가 처리 후 webhook/status 업데이트
    return {
        "status": "queued",
        "job_id": job_id,
        "files_received": len(files),
        "note": "stub: replace with real queue + worker",
    }


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
