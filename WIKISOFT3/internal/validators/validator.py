from typing import Any, Dict, List, Optional
import pandas as pd

from internal.validators.validation_layer1 import validate_layer1
from internal.validators.validation_layer_ai import validate_with_ai


def validate(
    parsed: Dict[str, Any], 
    matches: Dict[str, Any],
    diagnostic_answers: Optional[Dict[str, Any]] = None,
    use_ai: bool = True
) -> Dict[str, Any]:
    """유효성 검사 - 구조 검사 + L1 형식 검사 + AI 검사.
    
    L1 검증: 날짜/전화번호/이메일 형식, 필수값 누락, 음수 급여 등 (하드코딩)
    AI 검증: 컨텍스트 기반 판단 (진단 질문 응답 고려)
    """
    headers = parsed.get("headers") or []
    rows = parsed.get("rows") or []
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []
    errors: List[Dict[str, Any]] = []

    # 기본 구조 검사
    if not headers:
        warnings.append("헤더가 감지되지 않았습니다")
        checks.append({"name": "header_presence", "status": "fail"})
    else:
        checks.append({"name": "header_presence", "status": "pass"})

    checks.append({"name": "row_count", "status": "pass", "value": len(rows)})
    
    # L1 검증 (형식 검사)
    if headers and rows:
        try:
            # 매핑된 컬럼명으로 변환
            match_list = matches.get("matches", [])
            mapping = {}
            for m in match_list:
                if m.get("target"):
                    mapping[m["source"]] = m["target"]
            
            # DataFrame 생성
            df = pd.DataFrame(rows, columns=headers)
            
            # 컬럼명을 표준 필드명으로 변경 (원본도 유지)
            for orig, std in mapping.items():
                if orig in df.columns and std not in df.columns:
                    df[std] = df[orig]
            
            # L1 검증 실행
            l1_result = validate_layer1(df, diagnostic_answers or {})
            
            # 오류/경고 수집
            for e in l1_result.get("errors", []):
                errors.append({
                    "row": e.get("row", -1) + 2,  # 헤더 행 + 0-index 보정
                    "field": e.get("column", ""),
                    "message": e.get("error", ""),
                    "severity": "error"
                })
            
            for w in l1_result.get("warnings", []):
                warnings.append(w.get("warning", str(w)))
            
            checks.append({"name": "layer1_validation", "status": "pass" if not l1_result.get("errors") else "fail"})
            
        except Exception as e:
            checks.append({"name": "layer1_validation", "status": "error", "error": str(e)})
    
    # AI 검증 (컨텍스트 기반)
    ai_reasoning = []
    if use_ai and headers and rows:
        try:
            match_list = matches.get("matches", [])
            df = pd.DataFrame(rows, columns=headers)
            
            ai_result = validate_with_ai(df, match_list, diagnostic_answers)
            
            # AI 오류/경고 추가
            for e in ai_result.get("errors", []):
                errors.append({
                    "row": e.get("row", -1),
                    "field": e.get("field", ""),
                    "message": e.get("message", ""),
                    "reason": e.get("reason", ""),
                    "severity": "error",
                    "source": "ai"
                })
            
            for w in ai_result.get("warnings", []):
                warnings.append({
                    "row": w.get("row", -1),
                    "field": w.get("field", ""),
                    "message": w.get("message", ""),
                    "reason": w.get("reason", ""),
                    "source": "ai"
                })
            
            ai_reasoning = ai_result.get("ai_reasoning", [])
            checks.append({"name": "ai_validation", "status": "pass" if not ai_result.get("errors") else "warning"})
            
        except Exception as e:
            checks.append({"name": "ai_validation", "status": "error", "error": str(e)})

    return {
        "passed": len([e for e in errors if isinstance(e, dict)]) == 0 and len([w for w in warnings if isinstance(w, dict)]) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "ai_reasoning": ai_reasoning,
        "diagnostic_answers_received": bool(diagnostic_answers),
    }
