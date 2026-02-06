"""
Case Store: 성공적인 매칭/검증 케이스를 저장하고 유사 케이스 검색

- SQLite 기반 저장
- Few-shot Learning을 위한 예제 제공
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.database import get_db, get_cursor


class CaseStore:
    """성공적인 매칭/검증 케이스 저장소 (SQLite 기반)."""

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
        """케이스 저장."""
        case_id = self._generate_case_id(headers)
        timestamp = datetime.utcnow().isoformat()
        normalized_headers = [self._normalize_header(h) for h in headers]

        with get_cursor() as cur:
            cur.execute("""
                INSERT OR REPLACE INTO cases
                (case_id, timestamp, confidence, was_auto_approved,
                 headers, normalized_headers, matches, human_corrections, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id, timestamp, confidence, was_auto_approved,
                json.dumps(headers, ensure_ascii=False),
                json.dumps(normalized_headers, ensure_ascii=False),
                json.dumps(matches, ensure_ascii=False),
                json.dumps(human_corrections or {}, ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ))

        return case_id

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """케이스 조회."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    def find_similar_cases(
        self,
        headers: List[str],
        k: int = 5,
        min_overlap: float = 0.3
    ) -> List[Dict[str, Any]]:
        """유사한 케이스 검색 (헤더 패턴 기반)."""
        normalized_headers = {self._normalize_header(h) for h in headers}

        # 모든 케이스를 로드하여 비교
        db = get_db()
        all_cases = db.execute("SELECT * FROM cases").fetchall()

        similar_cases = []
        for row in all_cases:
            case_data = self._row_to_dict(row)
            case_headers = set(case_data.get("normalized_headers", []))

            # Jaccard-like 유사도
            intersection = len(normalized_headers & case_headers)
            union_size = len(normalized_headers | case_headers)
            similarity = intersection / union_size if union_size > 0 else 0

            if similarity >= min_overlap:
                similar_cases.append({
                    "case_id": case_data["case_id"],
                    "similarity": round(similarity, 3),
                    "overlap_count": intersection,
                    "case_data": case_data,
                })

        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases[:k]

    def find_by_header(self, header: str) -> List[Dict[str, Any]]:
        """특정 헤더를 포함하는 케이스 검색."""
        normalized = self._normalize_header(header)
        db = get_db()
        # JSON 배열 내 검색
        rows = db.execute(
            "SELECT * FROM cases WHERE normalized_headers LIKE ? ORDER BY timestamp DESC",
            (f'%"{normalized}"%',)
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_few_shot_examples(
        self,
        headers: List[str],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """Few-shot Learning용 예제 추출."""
        similar_cases = self.find_similar_cases(headers, k=k)
        examples = []

        for case in similar_cases:
            case_data = case["case_data"]

            example = {
                "input_headers": case_data.get("headers", [])[:10],
                "output_matches": [],
            }

            for match in case_data.get("matches", []):
                example["output_matches"].append({
                    "source": match.get("source", ""),
                    "target": match.get("target", ""),
                })

            if case_data.get("human_corrections"):
                example["human_corrections"] = case_data["human_corrections"]
                example["priority"] = "high"
            else:
                example["priority"] = "normal"

            examples.append(example)

        examples.sort(key=lambda x: 0 if x.get("priority") == "high" else 1)
        return examples

    def get_stats(self) -> Dict[str, Any]:
        """저장소 통계."""
        db = get_db()
        row = db.execute("""
            SELECT
                COUNT(*) as total_cases,
                SUM(CASE WHEN was_auto_approved THEN 1 ELSE 0 END) as auto_approved,
                SUM(CASE WHEN NOT was_auto_approved THEN 1 ELSE 0 END) as manual_corrected
            FROM cases
        """).fetchone()

        total = row["total_cases"] if row else 0
        auto = row["auto_approved"] if row else 0

        return {
            "total_cases": total,
            "auto_approved": auto,
            "manual_corrected": row["manual_corrected"] if row else 0,
            "auto_approval_rate": auto / total if total > 0 else 0,
        }

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        """sqlite3.Row → dict 변환"""
        d = dict(row)
        for field in ("headers", "normalized_headers", "matches", "human_corrections", "metadata"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    d[field] = [] if field in ("headers", "normalized_headers", "matches") else {}
        return d


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
