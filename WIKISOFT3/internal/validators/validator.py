from typing import Any, Dict, List


def validate(parsed: Dict[str, Any], matches: Dict[str, Any]) -> Dict[str, Any]:
    """간단한 유효성 검사 스텁.

    - 헤더 존재 여부와 행 수만 확인.
    - 추후: 레이어1/2 규칙·교차검증으로 확장.
    """
    headers = parsed.get("headers") or []
    rows = parsed.get("rows") or []
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if not headers:
        warnings.append("no headers detected")
        checks.append({"name": "header_presence", "status": "fail"})
    else:
        checks.append({"name": "header_presence", "status": "pass"})

    checks.append({"name": "row_count", "status": "pass", "value": len(rows)})

    return {
        "passed": len(warnings) == 0,
        "warnings": warnings,
        "checks": checks,
    }
