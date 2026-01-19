from typing import Any, Dict, List, Optional
import logging
import pandas as pd

from core.validators.validation_layer1 import validate_layer1
from core.validators.validation_layer2 import validate_layer2
from core.validators.validation_layer_ai import validate_with_ai
from core.validators.aggregator import get_aggregates_by_question_id
from core.ai.knowledge_base import save_training_example

logger = logging.getLogger(__name__)


def validate(
    parsed: Dict[str, Any],
    matches: Dict[str, Any],
    diagnostic_answers: Optional[Dict[str, Any]] = None,
    use_ai: bool = True,
    df: Optional[pd.DataFrame] = None,
    mode: str = "full"  # "roster" = 명부만, "full" = 전체 검증
) -> Dict[str, Any]:
    """유효성 검사 - 구조 검사 + L1 형식 검사 + AI 검사.

    L1 검증: 날짜/전화번호/이메일 형식, 필수값 누락, 음수 급여 등 (하드코딩)
    AI 검증: 컨텍스트 기반 판단 (진단 질문 응답 고려)

    모드:
        - "roster": 명부 형식 검증만 (L1만, 금액 검증 없음)
        - "full": 전체 검증 (L1 + L2 금액 비교 + AI)

    Args:
        df: 선택적 DataFrame (제공되면 재생성하지 않음, 성능 최적화용)
        mode: 검증 모드 ("roster" 또는 "full")
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

    # 인원수 비교는 Layer 2에서 상세하게 처리 (종업원구분별 비교)
    # 레거시 전체 인원수 비교 코드 제거 (중복 출력 방지)

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
            
            # L1 검증 실행 (mode, matches 전달)
            l1_result = validate_layer1(df, diagnostic_answers or {}, mode=mode, matches=match_list)
            
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
                except Exception as e:
                    # 학습 실패는 검증에 영향 없지만 로그는 남김
                    logger.warning(f"학습 이벤트 기록 실패 (검증 계속): {e}", exc_info=True)
            
        except Exception as e:
            checks.append({"name": "layer1_validation", "status": "error", "error": str(e)})

    # L2 검증: 사용자 입력값 vs 명부 집계값 비교
    # roster 모드에서도 인원수 비교를 위해 실행 (답변이 없는 질문은 자동 스킵됨)
    layer2_result = None
    if headers and rows and diagnostic_answers:
        try:
            # DataFrame이 없으면 생성
            if df is None:
                df = pd.DataFrame(rows, columns=headers)

            # 명부에서 집계값 계산 (종업원구분별 인원수, 금액 합계)
            calculated_aggregates = get_aggregates_by_question_id(df)

            # Layer 2 검증 실행
            layer2_result = validate_layer2(diagnostic_answers, calculated_aggregates)

            # Layer 2 경고/오류를 메인 결과에 병합
            for w in layer2_result.get("warnings", []):
                severity = w.get("severity", "warning")
                if severity == "high":
                    errors.append({
                        "row": None,
                        "field": w.get("question", "인원수"),
                        "message": w.get("message", ""),
                        "user_input": w.get("user_input"),
                        "calculated": w.get("calculated"),
                        "severity": "error",
                        "source": "layer2"
                    })
                elif severity != "info":
                    warnings.append({
                        "row": None,
                        "field": w.get("question", ""),
                        "message": w.get("message", ""),
                        "user_input": w.get("user_input"),
                        "calculated": w.get("calculated"),
                        "source": "layer2"
                    })

            status = layer2_result.get("status", "passed")
            checks.append({
                "name": "layer2_validation",
                "status": "pass" if status == "passed" else "warning" if status == "warnings" else "fail",
                "total_checks": layer2_result.get("total_checks", 0),
                "passed": layer2_result.get("passed", 0),
            })

            # Layer 2 비교 데이터 저장 (리포트용)
            layer2_result["calculated_aggregates"] = calculated_aggregates
            layer2_result["user_answers"] = diagnostic_answers
        except Exception as e:
            logger.warning(f"Layer 2 검증 실패: {e}", exc_info=True)
            checks.append({"name": "layer2_validation", "status": "error", "error": str(e)})

    # AI 검증 (컨텍스트 기반) - roster/full 모두 실행 (진단 답변 기반 검증)
    ai_reasoning = []
    if use_ai and headers and rows:
        try:
            match_list = matches.get("matches", [])
            # DataFrame 재사용 (성능 최적화)
            if df is None:
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
    def normalize_emp_info(emp_info: str) -> str:
        """emp_info를 정규화 (공백/소수점/접두사 제거, 형식 통일)"""
        if not emp_info:
            return ""
        result = emp_info.strip()
        # 접두사 제거 ("사원번호 ", "행 " 등)
        result = result.replace("사원번호 ", "").replace("행 ", "").strip()
        # 소수점 제거 (190001.0 → 190001)
        result = result.replace('.0', '')
        # 괄호 제거 ("190001 (행 1)" → "190001")
        if '(' in result:
            result = result.split('(')[0].strip()
        return result
    
    def deduplicate_all(error_list: List[Dict], warning_list: List[Dict]) -> tuple:
        """같은 사원번호 + 같은 필드 = 하나만 남기기
        
        - 에러와 경고가 같은 대상이면 에러만 남김 (더 심각)
        - 같은 종류(에러/경고)면 메시지 합치기
        """
        seen = {}  # key: (정규화된_emp_info, field)
        
        all_items = [(e, "error") for e in error_list] + [(w, "warning") for w in warning_list]
        
        for item, severity in all_items:
            if not isinstance(item, dict):
                continue
            
            emp_info = normalize_emp_info(item.get("emp_info", ""))
            field = (item.get("field") or item.get("column") or "unknown").strip()
            key = (emp_info, field)
            
            if key not in seen:
                # 새 항목 추가
                seen[key] = item.copy()
                seen[key]["severity"] = severity
            else:
                existing = seen[key]
                # 경고 → 에러로 업그레이드
                if existing.get("severity") == "warning" and severity == "error":
                    seen[key] = item.copy()
                    seen[key]["severity"] = severity
                # 같은 심각도면 메시지 보충
                elif existing.get("severity") == severity:
                    msg1 = existing.get("message", "")
                    msg2 = item.get("message", "")
                    if msg2 and msg2 not in msg1:
                        existing["message"] = f"{msg1}; {msg2}"
        
        # 분리해서 반환
        new_errors = []
        new_warnings = []
        for item in seen.values():
            sev = item.pop("severity")
            if sev == "error":
                new_errors.append(item)
            else:
                new_warnings.append(item)
        
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
        "layer2_comparison": layer2_result,  # 리포트용 비교 데이터
    }
