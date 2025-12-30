"""
Layer 2 검증: 챗봇 답변 vs 명부 자동계산 비교
사용자가 입력한 집계값이 실제 명부 데이터와 일치하는지 검증
"""
from typing import Dict, List, Any, Optional
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT2")


def validate_chatbot_answers(
    chatbot_answers: Dict[str, Any],
    calculated_aggregates: Dict[str, Any],
    tolerance_percent: float = 5.0
) -> Dict[str, Any]:
    """
    챗봇 답변과 자동 계산된 집계값 비교
    
    Args:
        chatbot_answers: 챗봇에서 수집한 답변 (q21~q30)
        calculated_aggregates: aggregate_calculator.py의 결과
        tolerance_percent: 허용 오차 비율 (기본 5%)
    
    Returns:
        {
            "status": "passed" | "warnings" | "failed",
            "total_checks": 8,
            "passed": 6,
            "warnings": [...]
        }
    """
    from internal.ai.diagnostic_questions import get_validation_questions
    
    # 퇴직자 전체 자동 계산 (q24 + q25 + q26)
    if all(k in chatbot_answers for k in ["q24", "q25", "q26"]):
        chatbot_answers["퇴직자전체"] = (
            float(chatbot_answers["q24"]) + 
            float(chatbot_answers["q25"]) + 
            float(chatbot_answers["q26"])
        )
    
    validation_questions = get_validation_questions()
    results = {
        "status": "passed",
        "total_checks": 0,
        "passed": 0,
        "warnings": []
    }
    
    for question in validation_questions:
        qid = question["id"]
        user_answer = chatbot_answers.get(qid)
        
        # 사용자가 답변하지 않은 경우 스킵
        if user_answer is None:
            continue
        
        results["total_checks"] += 1
        
        # validate_against 필드 파싱 (예: "counts_I26_I39[0]")
        validate_path = question["validate_against"]
        calculated_value = _extract_value(calculated_aggregates, validate_path)
        
        if calculated_value is None:
            # 계산값을 찾을 수 없는 경우
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_answer,
                "calculated": None,
                "severity": "info",
                "message": "명부에서 이 값을 자동 계산할 수 없습니다. 사용자 입력값을 신뢰합니다."
            })
            continue
        
        # 숫자 변환
        try:
            user_value = float(user_answer)
            calc_value = float(calculated_value)
        except (ValueError, TypeError):
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_answer,
                "calculated": calculated_value,
                "severity": "error",
                "message": "숫자 형식이 올바르지 않습니다."
            })
            continue
        
        # 비교
        diff = user_value - calc_value
        diff_percent = abs(diff / calc_value * 100) if calc_value != 0 else float('inf')
        
        if abs(diff) < 0.01:  # 거의 동일
            results["passed"] += 1
        elif diff_percent <= tolerance_percent:  # 허용 오차 내
            results["passed"] += 1
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_value,
                "calculated": calc_value,
                "diff": diff,
                "diff_percent": diff_percent,
                "severity": "low",
                "message": f"경미한 차이가 있습니다 ({diff_percent:.1f}%). 명부 계산값: {_format_value(calc_value, question)}"
            })
        else:  # 심각한 불일치
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_value,
                "calculated": calc_value,
                "diff": diff,
                "diff_percent": diff_percent,
                "severity": "high",
                "message": f"⭕ 명부에서 계산한 값은 {_format_value(calc_value, question)}이지만, 당신은 {_format_value(user_value, question)}이라고 입력하셨습니다. (차이: {diff_percent:.1f}%)"
            })
    
    # 전체 상태 결정
    if results["warnings"]:
        high_warnings = [w for w in results["warnings"] if w.get("severity") == "high"]
        if high_warnings:
            results["status"] = "failed"
        else:
            results["status"] = "warnings"
    
    return results


def _extract_value(data: Dict[str, Any], path: str) -> Optional[float]:
    """
    딕셔너리에서 값 추출
    예: "counts_I26_I39[0]" → data["counts_I26_I39"][0]
    """
    try:
        # 배열 인덱스 파싱
        if '[' in path:
            key, index_str = path.split('[')
            index = int(index_str.rstrip(']'))
            return data[key][index]
        else:
            return data[path]
    except (KeyError, IndexError, ValueError):
        return None


def _format_value(value: float, question: Dict[str, Any]) -> str:
    """값을 사람이 읽기 쉬운 형식으로 포맷팅"""
    format_type = question.get("format", "")
    
    if format_type == "currency":
        # 금액: 억/만 단위로 표시
        if value >= 100000000:  # 1억 이상
            return f"{value/100000000:.1f}억원"
        elif value >= 10000:  # 1만 이상
            return f"{value/10000:.0f}만원"
        else:
            return f"{value:,.0f}원"
    else:
        # 인원수 등: 그냥 숫자
        return f"{value:,.0f}{question.get('unit', '')}"


def get_validation_summary(validation_result: Dict[str, Any]) -> str:
    """검증 결과를 사람이 읽기 쉬운 문자열로 변환"""
    status = validation_result["status"]
    total = validation_result["total_checks"]
    passed = validation_result["passed"]
    warnings = validation_result["warnings"]
    
    if status == "passed":
        return f"✅ 모든 항목 일치 ({passed}/{total}개)"
    
    high_count = len([w for w in warnings if w.get("severity") == "high"])
    low_count = len([w for w in warnings if w.get("severity") == "low"])
    
    if status == "failed":
        return f"❌ 심각한 불일치 {high_count}개 발견 ({passed}/{total}개 일치)"
    else:  # warnings
        return f"⚠️  경미한 차이 {low_count}개 ({passed}/{total}개 일치)"


if __name__ == "__main__":
    # 테스트
    print("=== Layer 2 검증 테스트 ===\n")
    
    # 1. aggregate_calculator로 실제 계산
    from internal.generators.aggregate_calculator import aggregate_from_excel
    
    with open('20251223_세라젬_202512_확정급여채무평가_작성요청자료_기타장기 제외_메일발송.xls', 'rb') as f:
        content = f.read()
    
    calculated = aggregate_from_excel(content)
    print("📊 명부에서 자동 계산된 값:")
    print(f"  I26 (임원): {calculated['counts_I26_I39'][0]:.0f}명")
    print(f"  I27 (직원): {calculated['counts_I26_I39'][1]:.0f}명")
    
    # sums_I40_I51이 빈 문자열일 수 있으므로 안전하게 처리
    sum_val = calculated['sums_I40_I51'][0]
    if sum_val == '' or sum_val is None:
        print(f"  I41 (퇴직금): 계산 불가 (데이터 없음)")
    else:
        sum_val = float(sum_val) if isinstance(sum_val, str) else sum_val
        print(f"  I41 (퇴직금): {sum_val:,.0f}원")
    
    # 2. 챗봇 답변 시뮬레이션 (의도적으로 일부 틀리게)
    print("\n💬 챗봇 답변 (테스트):")
    chatbot_answers = {
        "q21": 20,  # 실제 17 → 불일치!
        "q22": 664,  # 정확함
        "q23": 69,  # 정확함
        "q24": 477,  # 정확함
        "q25": 26,  # 정확함
        "q26": 7000000000,  # 실제 67억 → 불일치!
        "q27": 691876810,  # 정확함
        "q28": 0  # 정확함
    }
    
    for qid, answer in chatbot_answers.items():
        print(f"  {qid}: {answer:,}")
    
    # 3. 검증 실행
    print("\n🔍 검증 중...\n")
    validation = validate_chatbot_answers(chatbot_answers, calculated, tolerance_percent=5.0)
    
    print(f"상태: {validation['status']}")
    print(f"검사 항목: {validation['total_checks']}개")
    print(f"통과: {validation['passed']}개")
    print(f"경고: {len(validation['warnings'])}개\n")
    
    print("=== 경고 내역 ===")
    for warning in validation["warnings"]:
        severity_icon = {"high": "🔴", "low": "🟡", "info": "ℹ️", "error": "❌"}.get(warning["severity"], "⚪")
        print(f"\n{severity_icon} [{warning['question_id']}] {warning['severity'].upper()}")
        print(f"   질문: {warning['question']}")
        print(f"   메시지: {warning['message']}")
    
    print(f"\n{get_validation_summary(validation)}")
