from typing import List, Dict, Any

def build_questions(validation_errors: List[Dict[str, Any]],
                    anomalies: List[Dict[str, Any]],
                    column_mapping: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    validation_errors와 anomalies를 받아 챗봇 질문 리스트를 만든다.
    Returns: {"questions": [...]}
    """
    questions: List[Dict[str, Any]] = []

    # 1) validation_errors → 질문화
    for err in validation_errors:
        # err 예시: {"row": 5, "errors": [{"column": "입사일자", "error": "필수 필드 누락"}]}
        row_idx = err.get("row")
        for detail in err.get("errors", []):
            col = detail.get("column")
            msg = detail.get("error", "")
            questions.append({
                "row": row_idx,
                "column": col,
                "issue": "검증 오류",
                "detail": msg,
                "confidence": 0.9,
                "level": "확실",   # 룰 기반 → 확실
                "message": f"{col}에서 오류가 발견되었습니다: {msg}",
                "actions": ["수정", "무시"]  # 필수 누락 등은 수정/무시만 제공
            })

    # 2) anomalies → 질문화
    for an in anomalies:
        # an 예시: {"row": 21, "column": "기준급여", "job_type": 1, "value": 13700000, "mean": 3500000, ...}
        row_idx = an.get("row")
        col = an.get("column")
        job_type = an.get("job_type")
        val = an.get("value")
        mean = an.get("mean")
        lower = an.get("lower_bound")
        upper = an.get("upper_bound")

        def _fmt(x):
            if isinstance(x, (int, float)):
                return f"{x:.1f}"
            return "N/A" if x is None else str(x)

        questions.append({
            "row": row_idx,
            "column": col,
            "issue": "이상치",
            "detail": f"직종={job_type}, 평균={_fmt(mean)}, 범위={_fmt(lower)}~{_fmt(upper)}, 현재={_fmt(val)}",
            "confidence": 0.8,
            "level": "권장",   # 통계적 → 권장
            "message": f"직종 {job_type}에서 {col} 값 {val}가 통계적 범위를 벗어났습니다. 확인해주세요.",
            "actions": ["승인", "수정", "무시"]
        })

    return {"questions": questions}