from typing import Any, Dict, List, Optional


def validate(
    parsed: Dict[str, Any], 
    matches: Dict[str, Any],
    diagnostic_answers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """유효성 검사 - 기본 구조 검사만 수행.
    
    진단 답변 기반 분석은 AI가 직접 수행하므로 여기서는 하드코딩 규칙 없음.
    """
    headers = parsed.get("headers") or []
    rows = parsed.get("rows") or []
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []

    # 기본 구조 검사만 수행
    if not headers:
        warnings.append("헤더가 감지되지 않았습니다")
        checks.append({"name": "header_presence", "status": "fail"})
    else:
        checks.append({"name": "header_presence", "status": "pass"})

    checks.append({"name": "row_count", "status": "pass", "value": len(rows)})
    
    # 진단 답변은 저장만 하고, 실제 분석은 AI가 수행
    # (validate.py의 check_diagnostic_consistency에서 AI 호출)

    return {
        "passed": len(warnings) == 0,
        "warnings": warnings,
        "checks": checks,
        "diagnostic_answers_received": bool(diagnostic_answers),
    }
