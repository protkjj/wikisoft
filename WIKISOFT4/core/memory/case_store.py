"""
Case Store: 성공적인 매칭/검증 케이스를 저장하고 유사 케이스 검색

- JSON 파일 기반 저장 (간단한 시작)
- 향후 FAISS/Chroma 벡터 DB로 업그레이드 가능
- Few-shot Learning을 위한 예제 제공
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib


# 케이스 저장 경로
CASE_STORE_PATH = Path(__file__).parent.parent.parent / "training_data" / "cases"
CASE_STORE_PATH.mkdir(parents=True, exist_ok=True)

# 인덱스 파일 (빠른 검색용)
INDEX_FILE = CASE_STORE_PATH / "index.json"


class CaseStore:
    """성공적인 매칭/검증 케이스 저장소."""
    
    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or CASE_STORE_PATH
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_path / "index.json"
        self._load_index()
    
    def _load_index(self):
        """인덱스 로드 (없으면 생성)."""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {
                "cases": [],
                "header_patterns": {},  # 헤더 패턴 → 케이스 ID 매핑
                "stats": {
                    "total_cases": 0,
                    "auto_approved": 0,
                    "manual_corrected": 0,
                }
            }
            self._save_index()
    
    def _save_index(self):
        """인덱스 저장."""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _generate_case_id(self, headers: List[str]) -> str:
        """헤더 기반 케이스 ID 생성."""
        header_str = "|".join(sorted(headers))
        return hashlib.md5(header_str.encode()).hexdigest()[:12]
    
    def _normalize_header(self, header: str) -> str:
        """헤더 정규화 (공백, 줄바꿈 제거)."""
        return " ".join(str(header).replace("\n", " ").split()).lower()
    
    def save_case(
        self,
        headers: List[str],
        matches: List[Dict[str, Any]],
        confidence: float,
        was_auto_approved: bool = True,
        human_corrections: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        케이스 저장.
        
        Args:
            headers: 원본 헤더 리스트
            matches: 매칭 결과 [{"source": "원본", "target": "표준필드", "confidence": 0.95}, ...]
            confidence: 전체 신뢰도 점수
            was_auto_approved: 자동 승인 여부 (True=사람 개입 없음)
            human_corrections: 사람이 수정한 매핑 {"원본헤더": "수정된_표준필드"}
            metadata: 추가 메타데이터 (회사명, 파일명 등)
        
        Returns:
            케이스 ID
        """
        case_id = self._generate_case_id(headers)
        timestamp = datetime.utcnow().isoformat()
        
        # 케이스 데이터
        case_data = {
            "case_id": case_id,
            "timestamp": timestamp,
            "headers": headers,
            "normalized_headers": [self._normalize_header(h) for h in headers],
            "matches": matches,
            "confidence": confidence,
            "was_auto_approved": was_auto_approved,
            "human_corrections": human_corrections or {},
            "metadata": metadata or {},
        }
        
        # 케이스 파일 저장
        case_file = self.store_path / f"{case_id}.json"
        with open(case_file, "w", encoding="utf-8") as f:
            json.dump(case_data, f, ensure_ascii=False, indent=2)
        
        # 인덱스 업데이트
        self._update_index(case_id, headers, was_auto_approved)
        
        return case_id
    
    def _update_index(self, case_id: str, headers: List[str], was_auto_approved: bool):
        """인덱스 업데이트."""
        # 케이스 추가 (중복 체크)
        existing_ids = {c["case_id"] for c in self.index["cases"]}
        if case_id not in existing_ids:
            self.index["cases"].append({
                "case_id": case_id,
                "header_count": len(headers),
                "was_auto_approved": was_auto_approved,
            })
            self.index["stats"]["total_cases"] += 1
            
            if was_auto_approved:
                self.index["stats"]["auto_approved"] += 1
            else:
                self.index["stats"]["manual_corrected"] += 1
        
        # 헤더 패턴 매핑
        for header in headers:
            normalized = self._normalize_header(header)
            if normalized not in self.index["header_patterns"]:
                self.index["header_patterns"][normalized] = []
            if case_id not in self.index["header_patterns"][normalized]:
                self.index["header_patterns"][normalized].append(case_id)
        
        self._save_index()
    
    def find_similar_cases(
        self,
        headers: List[str],
        k: int = 5,
        min_overlap: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        유사한 케이스 검색 (헤더 패턴 기반).
        
        Args:
            headers: 검색할 헤더 리스트
            k: 반환할 최대 케이스 수
            min_overlap: 최소 헤더 겹침 비율 (0.0 ~ 1.0)
        
        Returns:
            유사 케이스 리스트 (유사도 순 정렬)
        """
        normalized_headers = {self._normalize_header(h) for h in headers}
        case_scores = {}
        
        # 각 케이스의 헤더 겹침 정도 계산
        for header in normalized_headers:
            case_ids = self.index["header_patterns"].get(header, [])
            for case_id in case_ids:
                case_scores[case_id] = case_scores.get(case_id, 0) + 1
        
        # 유사도 계산 및 정렬
        similar_cases = []
        for case_id, overlap_count in case_scores.items():
            # Jaccard-like 유사도
            case_data = self.get_case(case_id)
            if not case_data:
                continue
            
            case_headers = set(case_data.get("normalized_headers", []))
            union_size = len(normalized_headers | case_headers)
            similarity = overlap_count / union_size if union_size > 0 else 0
            
            if similarity >= min_overlap:
                similar_cases.append({
                    "case_id": case_id,
                    "similarity": round(similarity, 3),
                    "overlap_count": overlap_count,
                    "case_data": case_data,
                })
        
        # 유사도 순 정렬
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases[:k]
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """케이스 조회."""
        case_file = self.store_path / f"{case_id}.json"
        if case_file.exists():
            with open(case_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def find_by_header(self, header: str) -> List[Dict[str, Any]]:
        """
        특정 헤더를 포함하는 케이스 검색.
        
        Args:
            header: 검색할 헤더 (정규화 전)
        
        Returns:
            해당 헤더가 있는 케이스 리스트
        """
        normalized = self._normalize_header(header)
        case_ids = self.index["header_patterns"].get(normalized, [])
        
        cases = []
        for case_id in case_ids:
            case_data = self.get_case(case_id)
            if case_data:
                cases.append(case_data)
        
        # 최신 케이스 우선
        cases.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return cases
    
    def get_few_shot_examples(
        self,
        headers: List[str],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Few-shot Learning용 예제 추출.
        유사 케이스에서 매칭 예제를 추출하여 GPT 프롬프트에 주입.
        
        Args:
            headers: 현재 처리할 헤더
            k: 예제 수
        
        Returns:
            Few-shot 예제 리스트
        """
        similar_cases = self.find_similar_cases(headers, k=k)
        examples = []
        
        for case in similar_cases:
            case_data = case["case_data"]
            
            # 매칭 예제 추출
            example = {
                "input_headers": case_data.get("headers", [])[:10],  # 최대 10개
                "output_matches": [],
            }
            
            for match in case_data.get("matches", []):
                example["output_matches"].append({
                    "source": match.get("source", ""),
                    "target": match.get("target", ""),
                })
            
            # 사람이 수정한 것이 있으면 더 가치 있음
            if case_data.get("human_corrections"):
                example["human_corrections"] = case_data["human_corrections"]
                example["priority"] = "high"  # 사람이 수정한 케이스 우선
            else:
                example["priority"] = "normal"
            
            examples.append(example)
        
        # 사람 수정 케이스 우선 정렬
        examples.sort(key=lambda x: 0 if x.get("priority") == "high" else 1)
        return examples
    
    def get_stats(self) -> Dict[str, Any]:
        """저장소 통계."""
        return {
            **self.index["stats"],
            "auto_approval_rate": (
                self.index["stats"]["auto_approved"] / self.index["stats"]["total_cases"]
                if self.index["stats"]["total_cases"] > 0 else 0
            ),
            "unique_header_patterns": len(self.index["header_patterns"]),
        }


# 글로벌 인스턴스
_case_store: Optional[CaseStore] = None


def get_case_store() -> CaseStore:
    """글로벌 CaseStore 인스턴스."""
    global _case_store
    if _case_store is None:
        _case_store = CaseStore()
    return _case_store


def save_successful_case(
    headers: List[str],
    matches: List[Dict[str, Any]],
    confidence: float,
    was_auto_approved: bool = True,
    human_corrections: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """편의 함수: 성공 케이스 저장."""
    store = get_case_store()
    return store.save_case(
        headers=headers,
        matches=matches,
        confidence=confidence,
        was_auto_approved=was_auto_approved,
        human_corrections=human_corrections,
        metadata=metadata,
    )


def find_similar_cases(headers: List[str], k: int = 5) -> List[Dict[str, Any]]:
    """편의 함수: 유사 케이스 검색."""
    store = get_case_store()
    return store.find_similar_cases(headers, k=k)


def get_few_shot_examples(headers: List[str], k: int = 3) -> List[Dict[str, Any]]:
    """편의 함수: Few-shot 예제 추출."""
    store = get_case_store()
    return store.get_few_shot_examples(headers, k=k)
