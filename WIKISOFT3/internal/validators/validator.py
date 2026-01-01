from typing import Any, Dict, List, Optional
import pandas as pd

from internal.validators.validation_layer1 import validate_layer1
from internal.validators.validation_layer_ai import validate_with_ai
from internal.ai.knowledge_base import save_training_example


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
                    "emp_info": e.get("emp_info", ""),  # 사원번호 정보 전달
                    "severity": "error"
                })
            
            for w in l1_result.get("warnings", []):
                if isinstance(w, dict):
                    warnings.append({
                        "row": w.get("row", -1) + 2 if w.get("row", -1) >= 0 else -1,
                        "field": w.get("column", ""),
                        "message": w.get("warning", ""),
                        "emp_info": w.get("emp_info", ""),
                        "source": "layer1"
                    })
                else:
                    warnings.append(str(w))
            
            checks.append({"name": "layer1_validation", "status": "pass" if not l1_result.get("errors") else "fail"})
            
            # Layer1이 발견한 오류를 AI 학습 데이터로 저장 (AI가 놓친 패턴 학습)
            if l1_result.get("errors"):
                try:
                    for err in l1_result.get("errors", [])[:5]:  # 최대 5개만
                        save_training_example(
                            input_data={
                                "error_type": err.get("column", "unknown"),
                                "error_message": err.get("error", ""),
                                "row_sample": rows[err.get("row", 0)] if err.get("row", 0) < len(rows) else {},
                            },
                            ai_response={"detected": False, "source": "layer1"},
                            human_correction={"should_detect": True, "rule": err.get("error", "")},
                            is_correct=False,  # AI가 놓쳤으므로
                            category="layer1_error"
                        )
                except Exception:
                    pass  # 학습 저장 실패해도 검증은 계속
            
        except Exception as e:
            checks.append({"name": "layer1_validation", "status": "error", "error": str(e)})
    
    # AI 검증 (컨텍스트 기반)
    ai_reasoning = []
    if use_ai and headers and rows:
        try:
            match_list = matches.get("matches", [])
            df = pd.DataFrame(rows, columns=headers)
            
            ai_result = validate_with_ai(df, match_list, diagnostic_answers)
            
            # AI 오류/경고 추가 (row를 +2 보정하여 Layer1과 통일)
            for e in ai_result.get("errors", []):
                ai_row = e.get("row", -1)
                # AI는 0-based index로 응답, Layer1과 통일을 위해 +2
                normalized_row = ai_row + 2 if isinstance(ai_row, int) and ai_row >= 0 else -1
                errors.append({
                    "row": normalized_row,
                    "field": e.get("field", ""),
                    "message": e.get("message", ""),
                    "reason": e.get("reason", ""),
                    "emp_info": e.get("emp_info", ""),
                    "severity": "error",
                    "source": "ai"
                })
            
            for w in ai_result.get("warnings", []):
                ai_row = w.get("row", -1)
                normalized_row = ai_row + 2 if isinstance(ai_row, int) and ai_row >= 0 else -1
                warnings.append({
                    "row": normalized_row,
                    "field": w.get("field", ""),
                    "message": w.get("message", ""),
                    "reason": w.get("reason", ""),
                    "emp_info": w.get("emp_info", ""),
                    "source": "ai"
                })
            
            ai_reasoning = ai_result.get("ai_reasoning", [])
            checks.append({"name": "ai_validation", "status": "pass" if not ai_result.get("errors") else "warning"})
            
        except Exception as e:
            checks.append({"name": "ai_validation", "status": "error", "error": str(e)})

    # ========================================
    # 중복 제거: 같은 사원번호 + 같은 필드면 하나로 통합
    # errors와 warnings를 합쳐서 처리 (같은 문제가 에러/경고로 중복되는 것 방지)
    # ========================================
    def normalize_message(msg: str) -> str:
        """메시지를 정규화해서 비교하기 쉽게
        
        비슷한 오류를 같은 것으로 처리:
        - "입사 나이 18세 미만" ≈ "입사연령 17세 미만" → 같은 오류 (입사|나이|미만)
        - "기준급여 최저임금 미달" ≈ "기준급여가 최저임금 미달 가능성" → 같은 오류
        """
        import re
        msg = msg.lower().strip()
        # 쉼표, 원 단위, 불필요한 문자 정규화
        msg = re.sub(r'[,원]', '', msg)
        # 연령/나이 동일 처리
        msg = msg.replace('연령', '나이')
        # 핵심 키워드 + 조건 키워드 추출
        type_keywords = ['미만', '초과', '미달', '음수', '누락', '중복', '형식오류', '불일치']
        field_keywords = ['입사', '나이', '급여', '최저임금', '생년월일', '사원번호', '성별', '기준급여']
        
        found_types = [k for k in type_keywords if k in msg]
        found_fields = [k for k in field_keywords if k in msg]
        
        # 조건 키워드가 있으면 필드+조건으로 구분
        if found_types and found_fields:
            return f"{'|'.join(sorted(found_fields))}:{'|'.join(sorted(found_types))}"
        elif found_fields:
            return '|'.join(sorted(found_fields))
        else:
            # 핵심 부분만 추출 (처음 30자)
            return msg[:30]
    
    def deduplicate_all(error_list: List[Dict], warning_list: List[Dict]) -> tuple:
        """에러와 경고를 합쳐서 중복 제거. 같은 (사원, 필드)면 더 심각한 것(에러)만 남김"""
        seen = {}  # key: (emp_info, field, normalized_msg)
        
        # 에러 먼저 처리 (우선순위 높음)
        for err in error_list:
            emp_info = err.get("emp_info", "") or f"row_{err.get('row', -1)}"
            field = err.get("field", "") or err.get("column", "") or "unknown"
            norm_msg = normalize_message(err.get("message", ""))
            key = (emp_info, field, norm_msg)
            
            if key not in seen:
                seen[key] = {"item": err.copy(), "is_error": True}
            else:
                # 이미 있으면 메시지 합치기
                existing = seen[key]["item"]
                new_msg = err.get("message", "")
                if new_msg and new_msg not in existing.get("message", ""):
                    existing["message"] = f"{existing['message']}; {new_msg}"
        
        # 경고 처리 (에러에서 이미 처리된 것은 스킵)
        for warn in warning_list:
            if not isinstance(warn, dict):
                continue
            emp_info = warn.get("emp_info", "") or f"row_{warn.get('row', -1)}"
            field = warn.get("field", "") or warn.get("column", "") or "unknown"
            norm_msg = normalize_message(warn.get("message", warn.get("warning", "")))
            key = (emp_info, field, norm_msg)
            
            if key not in seen:
                seen[key] = {"item": warn.copy(), "is_error": False}
            # 이미 에러로 있으면 경고는 무시 (에러가 더 심각)
        
        # 분리해서 반환
        new_errors = []
        new_warnings = []
        for data in seen.values():
            if data["is_error"]:
                new_errors.append(data["item"])
            else:
                new_warnings.append(data["item"])
        
        return new_errors, new_warnings
    
    # dict 형태의 warnings만 중복 제거 대상
    dict_warnings = [w for w in warnings if isinstance(w, dict)]
    str_warnings = [w for w in warnings if isinstance(w, str)]
    
    errors, dict_warnings = deduplicate_all(errors, dict_warnings)
    warnings = dict_warnings + str_warnings

    # AI 사용 여부 확인
    used_ai = any(c.get("name") == "ai_validation" and c.get("status") != "error" for c in checks)
    
    return {
        "passed": len(errors) == 0 and len(warnings) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "ai_reasoning": ai_reasoning,
        "diagnostic_answers_received": bool(diagnostic_answers),
        "used_ai": used_ai,
    }
