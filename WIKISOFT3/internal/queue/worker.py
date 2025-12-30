from __future__ import annotations

from typing import List

from rq import get_current_job

from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.agent.tool_registry import get_registry
from internal.memory.persistence import DecisionLog, SessionMemory


def process_batch(file_names: List[str], session_id: str = None) -> dict:
    """RQ 워커: 파일 배치 처리 (파서→매칭→검증→리포트)."""
    import uuid

    job = get_current_job()
    if not session_id:
        session_id = f"batch-{uuid.uuid4()}"
    if job:
        job.meta["files"] = file_names
        job.meta["session_id"] = session_id
        job.meta["progress"] = 0
        job.save_meta()

    registry = get_registry()
    session_mem = SessionMemory()
    decision_log = DecisionLog()
    total = len(file_names)
    results = []

    for idx, file_name in enumerate(file_names, start=1):
        try:
            file_bytes = b""  # TODO: 파일 로드 (S3/로컬 등)
            parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)
            matches = registry.call_tool("match_headers", parsed=parsed, sheet_type="재직자")
            validation = registry.call_tool("validate", parsed=parsed, matches=matches)
            confidence = estimate_confidence(parsed, matches, validation)
            anomalies = detect_anomalies(parsed, matches, validation)
            report = registry.call_tool("generate_report", validation=validation)

            decision_log.log_decision(session_id, {
                "file": file_name,
                "confidence": confidence["score"],
                "anomalies": anomalies["detected"],
                "recommendation": anomalies["recommendation"],
            })

            results.append({
                "file": file_name,
                "status": "success",
                "confidence": round(confidence["score"], 3),
                "has_issues": anomalies["detected"],
            })

        except Exception as e:  # noqa: BLE001
            decision_log.log_decision(session_id, {
                "file": file_name,
                "status": "error",
                "error": str(e),
            })
            results.append({
                "file": file_name,
                "status": "error",
                "error": str(e),
            })

        if job:
            job.meta["progress"] = int(idx / total * 100)
            job.save_meta()

    session_mem.save_session(session_id, {
        "files": file_names,
        "results": results,
        "completed": True,
    })

    return {
        "session_id": session_id,
        "processed": len([r for r in results if r["status"] == "success"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "files": results,
    }
