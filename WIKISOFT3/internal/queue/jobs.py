from __future__ import annotations

import os
import uuid
from typing import Dict, List, Literal, Optional

from redis import Redis
from rq import Queue, Retry
from rq.job import Job

JobStatus = Literal["queued", "running", "completed", "failed"]

# 인메모리 백업 스토어 (Redis/RQ 미사용 시)
_JOB_STORE: Dict[str, Dict] = {}


def _get_queue() -> Optional[Queue]:
    """Redis 큐 연결 시도. 실패하면 None 반환."""
    redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
    try:
        conn = Redis.from_url(redis_url)
        # 실제 연결 테스트
        conn.ping()
        return Queue("wikisoft3", connection=conn, default_timeout=600)
    except Exception:  # noqa: BLE001
        return None


def enqueue_jobs(file_names: List[str]) -> str:
    """작업 큐에 등록. Redis 없으면 인메모리 폴백."""
    q = _get_queue()
    if q:
        try:
            job = q.enqueue("internal.queue.worker.process_batch", file_names, retry=Retry(max=1, interval=[10]))
            return job.get_id()
        except Exception:  # noqa: BLE001
            pass  # Redis 연결 실패 시 폴백

    # 인메모리 폴백
    job_id = f"job-{uuid.uuid4()}"
    _JOB_STORE[job_id] = {
        "status": "queued",
        "files": file_names,
        "progress": 0,
        "result": None,
        "error": None,
    }
    return job_id


def get_job(job_id: str) -> Dict | None:
    q = _get_queue()
    if q:
        try:
            job = Job.fetch(job_id, connection=q.connection)
            return {
                "status": job.get_status(),
                "progress": job.meta.get("progress", 0),
                "result": job.result,
                "error": job.meta.get("error"),
                "files": job.meta.get("files"),
            }
        except Exception:  # noqa: BLE001
            return None
    return _JOB_STORE.get(job_id)


def update_job(job_id: str, status: JobStatus, progress: int = 0, result=None, error=None) -> None:
    q = _get_queue()
    if q:
        try:
            job = Job.fetch(job_id, connection=q.connection)
            job.meta["progress"] = progress
            if error:
                job.meta["error"] = error
            job.save_meta()
            if status in ("completed", "failed"):
                job.set_status(status)
                if status == "completed":
                    job._result = result  # noqa: SLF001
                if status == "failed" and error:
                    job._exc_info = str(error)  # noqa: SLF001
                job.save()
        except Exception:  # noqa: BLE001
            pass
        return

    if job_id not in _JOB_STORE:
        return
    _JOB_STORE[job_id].update({
        "status": status,
        "progress": progress,
        "result": result,
        "error": error,
    })
