"""
Validation History Store

검증 이력 저장 및 조회 (SQLite 기반)
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.database import get_db, get_cursor


class ValidationHistoryStore:
    """검증 이력 저장소 (SQLite 기반)"""

    def add(
        self,
        filename: str,
        status: str,
        confidence: float,
        error_count: int,
        warning_count: int,
        row_count: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """검증 이력 추가"""
        # 분기 결정
        if error_count > 0:
            action = "rejected"
        elif confidence >= 0.9:
            action = "auto_approve"
        else:
            action = "needs_review"

        # 메시지 생성
        if action == "auto_approve":
            message = f"자동 승인 (신뢰도 {confidence:.1%})"
        elif action == "rejected":
            message = f"검증 실패: {error_count}개 오류 발견"
        else:
            message = f"수동 검토 필요 (신뢰도 {confidence:.1%})"

        record = {
            "id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
            "company_name": company_name,
            "status": status,
            "action": action,
            "confidence": confidence,
            "message": message,
            "error_count": error_count,
            "warning_count": warning_count,
            "row_count": row_count,
            "user_id": user_id,
            "session_id": session_id,
            "run_id": str(uuid4())[:8],
            "details": details or {},
        }

        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO validation_history
                (id, timestamp, filename, company_name, status, action, confidence, message,
                 error_count, warning_count, row_count, user_id, session_id, run_id, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["timestamp"], record["filename"],
                record["company_name"], record["status"], record["action"], record["confidence"],
                record["message"], record["error_count"], record["warning_count"],
                record["row_count"], record["user_id"], record["session_id"],
                record["run_id"], json.dumps(record["details"], ensure_ascii=False, default=str),
            ))

        return record

    def update_by_session(
        self,
        session_id: str,
        status: str,
        confidence: float,
        error_count: int,
        warning_count: int,
    ) -> bool:
        """같은 세션의 최신 이력을 업데이트 (재검증 시 사용)

        Returns:
            True: 업데이트 성공, False: 해당 세션 이력 없음
        """
        db = get_db()
        row = db.execute(
            "SELECT id FROM validation_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1",
            (session_id,)
        ).fetchone()

        if not row:
            return False

        # 분기 재결정
        if error_count > 0:
            action = "rejected"
        elif confidence >= 0.9:
            action = "auto_approve"
        else:
            action = "needs_review"

        # 메시지 재생성
        if action == "auto_approve":
            message = f"자동 승인 (신뢰도 {confidence:.1%})"
        elif action == "rejected":
            message = f"검증 실패: {error_count}개 오류 발견"
        else:
            message = f"수동 검토 필요 (신뢰도 {confidence:.1%})"

        with get_cursor() as cur:
            cur.execute("""
                UPDATE validation_history
                SET status = ?, action = ?, confidence = ?, message = ?,
                    error_count = ?, warning_count = ?,
                    timestamp = ?
                WHERE id = ?
            """, (
                status, action, confidence, message,
                error_count, warning_count,
                datetime.now(timezone.utc).isoformat(),
                row["id"],
            ))

        return True

    def get_latest(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 이력 조회"""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM validation_history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_by_user(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """사용자별 이력 조회"""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM validation_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        db = get_db()
        row = db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN action = 'auto_approve' THEN 1 ELSE 0 END) as auto_approve,
                SUM(CASE WHEN action = 'needs_review' THEN 1 ELSE 0 END) as needs_review,
                SUM(CASE WHEN action = 'rejected' THEN 1 ELSE 0 END) as rejected,
                AVG(confidence) as avg_confidence
            FROM validation_history
        """).fetchone()

        if not row or row["total"] == 0:
            return {
                "total": 0,
                "auto_approve": 0,
                "needs_review": 0,
                "rejected": 0,
                "avg_confidence": 0,
            }

        return {
            "total": row["total"],
            "auto_approve": row["auto_approve"],
            "needs_review": row["needs_review"],
            "rejected": row["rejected"],
            "avg_confidence": row["avg_confidence"] or 0,
        }

    @staticmethod
    def _row_to_dict(row: Any) -> Dict[str, Any]:
        """sqlite3.Row → dict 변환"""
        d = dict(row)
        if d.get("details"):
            try:
                d["details"] = json.loads(d["details"])
            except (json.JSONDecodeError, TypeError):
                d["details"] = {}
        return d


# Global singleton
_validation_history: ValidationHistoryStore | None = None


def get_validation_history() -> ValidationHistoryStore:
    """검증 이력 저장소 싱글톤 반환"""
    global _validation_history
    if _validation_history is None:
        _validation_history = ValidationHistoryStore()
    return _validation_history
