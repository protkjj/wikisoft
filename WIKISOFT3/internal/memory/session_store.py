"""
세션 기반 검증 결과 저장소

글로벌 변수 대신 세션 ID로 결과를 분리 저장.
동시 사용자가 있어도 데이터가 섞이지 않음.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from threading import Lock

logger = logging.getLogger(__name__)


class SessionStore:
    """인메모리 세션 저장소 (프로덕션에서는 Redis 권장)"""

    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ttl = timedelta(minutes=ttl_minutes)

    def create_session(self) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._store[session_id] = {
                "created_at": datetime.now(),
                "validation_result": None,
                "parsed_data": None,
                "diagnostic_answers": None,
            }
        return session_id

    def get(self, session_id: str, key: str) -> Optional[Any]:
        """세션 데이터 조회"""
        with self._lock:
            session = self._store.get(session_id)
            if not session:
                return None
            # TTL 체크
            if datetime.now() - session["created_at"] > self._ttl:
                del self._store[session_id]
                return None
            return session.get(key)

    def set(self, session_id: str, key: str, value: Any) -> bool:
        """세션 데이터 저장"""
        with self._lock:
            if session_id not in self._store:
                return False
            self._store[session_id][key] = value
            return True

    def get_or_create(self, session_id: Optional[str]) -> str:
        """세션 ID가 없거나 만료되었으면 새로 생성"""
        if session_id:
            with self._lock:
                session = self._store.get(session_id)
                if session and datetime.now() - session["created_at"] <= self._ttl:
                    return session_id
        return self.create_session()

    def cleanup_expired(self) -> int:
        """만료된 세션 정리"""
        now = datetime.now()
        removed = 0
        with self._lock:
            expired = [
                sid for sid, data in self._store.items()
                if now - data["created_at"] > self._ttl
            ]
            for sid in expired:
                del self._store[sid]
                removed += 1
        if removed > 0:
            logger.info(f"세션 정리: {removed}개 만료된 세션 제거 (남은 세션: {len(self._store)}개)")
        return removed

    async def start_cleanup_task(self, interval_minutes: int = 10):
        """백그라운드 세션 정리 작업 시작"""
        logger.info(f"세션 자동 정리 시작 (주기: {interval_minutes}분)")
        while True:
            await asyncio.sleep(interval_minutes * 60)
            try:
                self.cleanup_expired()
            except Exception as e:
                logger.error(f"세션 정리 중 오류: {e}", exc_info=True)


# 싱글톤 인스턴스
session_store = SessionStore(ttl_minutes=30)
