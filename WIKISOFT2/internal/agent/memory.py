"""
Memory System: 패턴 저장 및 학습

Agent가 경험한 패턴을 저장하고 재사용합니다.
현재: 인메모리 (메모리 기반)
미래: Redis / Vector DB 연결
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib


@dataclass
class MemoryEntry:
    """메모리 항목"""
    id: str
    type: str  # "pattern", "error", "success", "rule"
    key: str  # 패턴의 고유 키
    data: Dict[str, Any]
    confidence: float = 0.5
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "type": self.type,
            "key": self.key,
            "data": self.data,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }


class MemorySystem:
    """
    Agent 메모리 시스템
    
    학습된 패턴, 규칙, 오류를 저장합니다.
    """
    
    def __init__(self, max_entries: int = 1000):
        """
        초기화
        
        Args:
            max_entries: 최대 저장 항목 수
        """
        self.max_entries = max_entries
        self._memory: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, List[str]] = {
            "pattern": [],
            "error": [],
            "success": [],
            "rule": []
        }
    
    def remember(
        self,
        type: str,
        key: str,
        data: Dict[str, Any],
        confidence: float = 0.5
    ) -> str:
        """
        패턴/규칙 저장
        
        Args:
            type: 메모리 타입 (pattern, error, success, rule)
            key: 패턴의 고유 키
            data: 저장할 데이터
            confidence: 신뢰도
        
        Returns:
            메모리 ID
        """
        # 이미 존재하는지 확인
        existing_id = self.find_by_key(key, type)
        if existing_id:
            # 기존 항목 업데이트
            entry = self._memory[existing_id]
            entry.confidence = max(entry.confidence, confidence)
            entry.usage_count += 1
            entry.last_used = datetime.now().isoformat()
            return existing_id
        
        # 새 항목 생성
        entry_id = hashlib.md5(f"{type}_{key}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        entry = MemoryEntry(
            id=entry_id,
            type=type,
            key=key,
            data=data,
            confidence=confidence
        )
        
        # 저장소가 가득 찬 경우 가장 오래되고 신뢰도 낮은 항목 삭제
        if len(self._memory) >= self.max_entries:
            self._evict_oldest()
        
        self._memory[entry_id] = entry
        self._index[type].append(entry_id)
        
        return entry_id
    
    def recall(self, key: str, type: Optional[str] = None) -> Optional[MemoryEntry]:
        """
        패턴 조회
        
        Args:
            key: 패턴 키
            type: 메모리 타입 (선택)
        
        Returns:
            MemoryEntry 또는 None
        """
        entry_id = self.find_by_key(key, type)
        if entry_id:
            entry = self._memory[entry_id]
            entry.usage_count += 1
            entry.last_used = datetime.now().isoformat()
            return entry
        return None
    
    def find_by_key(self, key: str, type: Optional[str] = None) -> Optional[str]:
        """
        키로 메모리 ID 찾기
        
        Args:
            key: 패턴 키
            type: 메모리 타입 (선택)
        
        Returns:
            메모리 ID 또는 None
        """
        if type:
            # 특정 타입에서만 검색
            for entry_id in self._index.get(type, []):
                if self._memory[entry_id].key == key:
                    return entry_id
        else:
            # 모든 타입에서 검색
            for entry in self._memory.values():
                if entry.key == key:
                    return entry.id
        
        return None
    
    def search(
        self,
        query: str,
        type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[MemoryEntry]:
        """
        키워드로 검색
        
        Args:
            query: 검색 쿼리
            type: 메모리 타입 (선택)
            min_confidence: 최소 신뢰도
        
        Returns:
            일치하는 항목들
        """
        results = []
        
        for entry in self._memory.values():
            # 타입 필터
            if type and entry.type != type:
                continue
            
            # 신뢰도 필터
            if entry.confidence < min_confidence:
                continue
            
            # 키워드 매칭
            if query.lower() in entry.key.lower():
                results.append(entry)
        
        # 신뢰도 내림차순 정렬
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def get_top_patterns(
        self,
        type: str,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        상위 패턴 조회
        
        Args:
            type: 메모리 타입
            limit: 반환할 항목 수
        
        Returns:
            신뢰도가 높은 항목들
        """
        entries = [
            self._memory[eid] for eid in self._index.get(type, [])
        ]
        
        # 신뢰도 × 사용 횟수로 정렬
        entries.sort(
            key=lambda x: x.confidence * (1 + x.usage_count),
            reverse=True
        )
        
        return entries[:limit]
    
    def forget(self, entry_id: str) -> bool:
        """
        특정 메모리 삭제
        
        Args:
            entry_id: 메모리 ID
        
        Returns:
            True if successful
        """
        if entry_id not in self._memory:
            return False
        
        entry = self._memory[entry_id]
        del self._memory[entry_id]
        
        # 인덱스에서도 제거
        if entry_id in self._index.get(entry.type, []):
            self._index[entry.type].remove(entry_id)
        
        return True
    
    def forget_all(self, type: Optional[str] = None) -> int:
        """
        메모리 전체 또는 특정 타입 삭제
        
        Args:
            type: 메모리 타입 (선택, None이면 전체)
        
        Returns:
            삭제된 항목 수
        """
        if type:
            # 특정 타입 삭제
            count = 0
            for entry_id in self._index.get(type, []).copy():
                self.forget(entry_id)
                count += 1
            return count
        else:
            # 전체 삭제
            count = len(self._memory)
            self._memory.clear()
            for key in self._index:
                self._index[key].clear()
            return count
    
    def _evict_oldest(self) -> None:
        """
        가장 오래되고 신뢰도가 낮은 항목 삭제
        """
        # 사용 횟수와 신뢰도를 고려하여 점수 계산
        entries = list(self._memory.values())
        entries.sort(
            key=lambda x: (x.confidence * x.usage_count, x.last_used),
            reverse=False
        )
        
        # 가장 점수가 낮은 항목 삭제
        if entries:
            self.forget(entries[0].id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        메모리 통계
        
        Returns:
            {
                "total_entries": int,
                "by_type": {type: count},
                "avg_confidence": float,
                "most_used": MemoryEntry,
            }
        """
        stats = {
            "total_entries": len(self._memory),
            "by_type": {
                type: len(self._index[type]) for type in self._index
            },
            "avg_confidence": 0.0,
            "most_used": None,
            "usage_count": sum(e.usage_count for e in self._memory.values()),
        }
        
        if self._memory:
            avg_conf = sum(e.confidence for e in self._memory.values()) / len(self._memory)
            stats["avg_confidence"] = round(avg_conf, 3)
            
            most_used = max(self._memory.values(), key=lambda x: x.usage_count)
            stats["most_used"] = most_used.to_dict()
        
        return stats
    
    def export(self) -> Dict[str, Any]:
        """
        메모리 전체 내보내기 (JSON 호환)
        
        Returns:
            메모리 전체 데이터
        """
        return {
            "total": len(self._memory),
            "entries": [e.to_dict() for e in self._memory.values()],
            "stats": self.get_stats(),
        }
    
    def import_data(self, data: Dict[str, Any]) -> int:
        """
        메모리 데이터 임포트
        
        Args:
            data: 임포트할 데이터
        
        Returns:
            임포트된 항목 수
        """
        count = 0
        for entry_data in data.get("entries", []):
            self.remember(
                type=entry_data["type"],
                key=entry_data["key"],
                data=entry_data["data"],
                confidence=entry_data["confidence"]
            )
            count += 1
        return count


# 전역 인스턴스
_global_memory = MemorySystem(max_entries=1000)


def get_memory() -> MemorySystem:
    """전역 MemorySystem 조회"""
    return _global_memory
