"""
세션 기반 검증 결과 저장소

Redis 기반 세션 스토어 (Redis 없으면 인메모리로 자동 폴백)
- 서버 재시작해도 세션 유지
- 다중 서버 환경에서 세션 공유
- TTL 자동 관리
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from threading import Lock

logger = logging.getLogger(__name__)


class BaseSessionStore(ABC):
    """세션 스토어 추상 클래스"""

    @abstractmethod
    def create_session(self) -> str:
        """새 세션 생성"""
        pass

    @abstractmethod
    def get(self, session_id: str, key: str) -> Optional[Any]:
        """세션 데이터 조회"""
        pass

    @abstractmethod
    def set(self, session_id: str, key: str, value: Any) -> bool:
        """세션 데이터 저장"""
        pass

    @abstractmethod
    def get_or_create(self, session_id: Optional[str]) -> str:
        """세션 ID가 없거나 만료되었으면 새로 생성"""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """만료된 세션 정리"""
        pass

    @abstractmethod
    async def start_cleanup_task(self, interval_minutes: int = 10):
        """백그라운드 세션 정리 작업"""
        pass


class RedisSessionStore(BaseSessionStore):
    """Redis 기반 세션 저장소"""

    def __init__(self, redis_url: str, ttl_minutes: int = 30):
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._ttl_seconds = ttl_minutes * 60
            # 연결 테스트
            self._redis.ping()
            logger.info(f"✅ Redis 세션 스토어 초기화 완료 (TTL: {ttl_minutes}분)")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise

    def _get_key(self, session_id: str, field: str = "") -> str:
        """Redis 키 생성"""
        if field:
            return f"session:{session_id}:{field}"
        return f"session:{session_id}"

    def create_session(self) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        # 세션 메타데이터 저장
        self._redis.hset(
            self._get_key(session_id),
            mapping={
                "created_at": datetime.now().isoformat(),
                "validation_result": "",
                "parsed_data": "",
                "diagnostic_answers": ""
            }
        )
        # TTL 설정
        self._redis.expire(self._get_key(session_id), self._ttl_seconds)
        return session_id

    def get(self, session_id: str, key: str) -> Optional[Any]:
        """세션 데이터 조회"""
        try:
            value = self._redis.hget(self._get_key(session_id), key)
            if value is None or value == "":
                return None
            # JSON 역직렬화
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"세션 조회 오류 ({session_id}): {e}")
            return None

    def set(self, session_id: str, key: str, value: Any) -> bool:
        """세션 데이터 저장"""
        try:
            # 세션 존재 확인
            if not self._redis.exists(self._get_key(session_id)):
                return False

            # JSON 직렬화
            if value is not None and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            elif value is None:
                value = ""

            self._redis.hset(self._get_key(session_id), key, value)
            # TTL 갱신
            self._redis.expire(self._get_key(session_id), self._ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"세션 저장 오류 ({session_id}): {e}")
            return False

    def get_or_create(self, session_id: Optional[str]) -> str:
        """세션 ID가 없거나 만료되었으면 새로 생성"""
        if session_id and self._redis.exists(self._get_key(session_id)):
            return session_id
        return self.create_session()

    def cleanup_expired(self) -> int:
        """만료된 세션 정리 (Redis는 TTL로 자동 관리)"""
        # Redis는 TTL로 자동 정리되므로 수동 정리 불필요
        # 통계 목적으로 현재 세션 수만 반환
        try:
            session_keys = self._redis.keys("session:*")
            active_sessions = len(set(k.split(":")[1] for k in session_keys if len(k.split(":")) > 1))
            logger.info(f"현재 활성 세션: {active_sessions}개 (Redis TTL 자동 관리)")
            return 0
        except Exception as e:
            logger.error(f"세션 통계 조회 오류: {e}")
            return 0

    async def start_cleanup_task(self, interval_minutes: int = 10):
        """백그라운드 통계 로깅 (Redis는 자동 만료)"""
        logger.info(f"Redis 세션 모니터링 시작 (주기: {interval_minutes}분)")
        while True:
            await asyncio.sleep(interval_minutes * 60)
            try:
                self.cleanup_expired()  # 통계만 출력
            except Exception as e:
                logger.error(f"세션 모니터링 오류: {e}", exc_info=True)


class InMemorySessionStore(BaseSessionStore):
    """인메모리 세션 저장소 (폴백용)"""

    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ttl = timedelta(minutes=ttl_minutes)
        logger.warning("⚠️ 인메모리 세션 스토어 사용 (Redis 미설정). 프로덕션에서는 Redis 사용 권장")

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


def create_session_store(ttl_minutes: int = 30) -> BaseSessionStore:
    """
    환경변수에 따라 적절한 세션 스토어 생성

    - REDIS_URL 있음 → RedisSessionStore
    - REDIS_URL 없음 → InMemorySessionStore (폴백)
    """
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        try:
            return RedisSessionStore(redis_url=redis_url, ttl_minutes=ttl_minutes)
        except Exception as e:
            logger.warning(f"Redis 초기화 실패, 인메모리로 폴백: {e}")
            return InMemorySessionStore(ttl_minutes=ttl_minutes)
    else:
        logger.info("REDIS_URL 미설정, 인메모리 세션 스토어 사용")
        return InMemorySessionStore(ttl_minutes=ttl_minutes)


# 싱글톤 인스턴스 (자동으로 Redis 또는 인메모리 선택)
session_store = create_session_store(ttl_minutes=30)
