"""
Memory & Persistence: Redis 세션 + 결정 로그 + Audit 스키마
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from redis import Redis


class SessionMemory:
    """Redis 기반 세션 메모리."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = Redis.from_url(redis_url)
            self.redis.ping()
        except Exception:
            self.redis = None

    def save_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        if not self.redis:
            return False
        try:
            self.redis.setex(f"session:{session_id}", ttl, json.dumps(data))
            return True
        except Exception:
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.redis:
            return None
        try:
            data = self.redis.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        if not self.redis:
            return False
        try:
            self.redis.delete(f"session:{session_id}")
            return True
        except Exception:
            return False


class DecisionLog:
    """Agent 결정 로그 저장."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = Redis.from_url(redis_url)
        except Exception:
            self.redis = None

    def log_decision(self, session_id: str, decision: Dict[str, Any]) -> bool:
        if not self.redis:
            return False
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
                **decision,
            }
            self.redis.lpush(f"decisions:{session_id}", json.dumps(entry))
            return True
        except Exception:
            return False

    def get_decisions(self, session_id: str) -> list[Dict[str, Any]]:
        if not self.redis:
            return []
        try:
            raw = self.redis.lrange(f"decisions:{session_id}", 0, -1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []


class AuditSchema:
    """Audit trail 스키마 정의 (PostgreSQL 예정)."""

    # 아직 인메모리/Redis 저장소만 구현. Postgres는 v3.1 로드맵
    AUDIT_FIELDS = {
        "timestamp": "datetime",
        "session_id": "string",
        "user_id": "string",
        "action": "string",
        "resource": "string",
        "result": "string",
        "error": "string",
        "trace_id": "string",
    }

    @staticmethod
    def to_dict(timestamp: str, session_id: str, user_id: str, action: str, resource: str, result: str, error: Optional[str] = None, trace_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "timestamp": timestamp,
            "session_id": session_id,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "error": error,
            "trace_id": trace_id,
        }
