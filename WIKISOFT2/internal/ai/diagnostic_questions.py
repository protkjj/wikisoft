"""
진단 질문 시스템 (24개)
- q1-q14: 기본 14개 질문 (WIKISOFT1 동일)
- q21-q26: 6개 인원 집계 질문 (재직자 3개 + 퇴직자 3개)
- q27-q30: 4개 금액 집계 질문 (Layer 2 검증)

참고: 퇴직자 전체 인원은 q24+q25+q26으로 자동 계산
"""
from typing import List, Dict, Any


# ========== 기본 14개 질문 (WIKISOFT1과 동일) ==========
BASIC_QUESTIONS = [
    {
        "id": "q1",
        "type": "choice",
        "category": "data_quality",
        "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?",
        "choices": ["예", "아니오"],
        "mapping": "사외적립자산"
    },
    {
        "id": "q2",
        "type": "choice",
        "category": "data_quality",
        "question": "정년 - 정년은 만 60 세 입니까?",
        "choices": ["예", "아니오"],
        "mapping": "정년"
    },
    {
        "id": "q3",
        "type": "choice",
        "category": "data_quality",
        "question": "임금피크제 - 임금피크제 미적용 기업입니까?",
        "choices": ["예", "아니오"],
        "mapping": "임금피크제"
    },
    {
        "id": "q4",
        "type": "choice",
        "category": "data_quality",
        "question": "기타장기종업원급여 - 기타장기종업원급여 미적용 기업입니까?",
        "choices": ["예", "아니오"],
        "mapping": "기타장기급여"
    },
    {
        "id": "q5",
        "type": "choice",
        "category": "data_quality",
        "question": "퇴직금제도 - 퇴직금제도는 법정제를 적용합니까?",
        "choices": ["예", "아니오"],
        "mapping": "퇴직금제도"
    },
    {
        "id": "q6",
        "type": "choice",
        "category": "data_quality",
        "question": "연봉제/호봉제 - 근무기간에 따른 호봉 미적용 기업입니까?",
        "choices": ["예", "아니오"],
        "mapping": "급여체계"
    },
    {
        "id": "q7",
        "type": "choice",
        "category": "data_quality",
        "question": "채권 등급 - 할인율 산출기준 채권 회사채 AA++ 적용 기업입니까?",
        "choices": ["예", "아니오"],
        "mapping": "할인율기준"
    },
    {
        "id": "q8",
        "type": "choice",
        "category": "data_quality",
        "question": "1년 미만 재직자 - 1년 미만 재직자도 기재 하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "1년미만재직자"
    },
    {
        "id": "q9",
        "type": "choice",
        "category": "data_quality",
        "question": "퇴직금 추계액 - 모든 재직자의 당년도, 차년도 퇴직금 추계액을 입력하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "퇴직금추계액"
    },
    {
        "id": "q10",
        "type": "choice",
        "category": "data_quality",
        "question": "기준급여 - 3개월 미만 재직자의 경우 한달 근무 시 지급받는 급여로 기재하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "기준급여"
    },
    {
        "id": "q11",
        "type": "choice",
        "category": "data_quality",
        "question": "평가기준일 퇴사자 - 평가기준일 발생 퇴직금을 비용 처리 하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "평가기준일퇴사자비용"
    },
    {
        "id": "q12",
        "type": "choice",
        "category": "data_quality",
        "question": "재직자명부 - 평가기준일 퇴사자를 제외 하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "재직자명부퇴사자제외"
    },
    {
        "id": "q13",
        "type": "choice",
        "category": "data_quality",
        "question": "중간정산 - 근퇴법 시행령 제3조에 해당합니까?",
        "choices": ["예", "아니오"],
        "mapping": "중간정산사유"
    },
    {
        "id": "q14",
        "type": "choice",
        "category": "data_quality",
        "question": "퇴직자명부 - 평가기준일 퇴사자를 포함하셨습니까?",
        "choices": ["예", "아니오"],
        "mapping": "퇴직자명부포함"
    }
]


# ========== 인원 집계 질문 (q21-q26) ==========
HEADCOUNT_AGGREGATES = [
    {
        "id": "q21",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "임원 인원은 몇 명인가요?",
        "mapping": "임원인원",
        "unit": "명",
        "validate_against": "headcount"
    },
    {
        "id": "q22",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "일반직원 인원은 몇 명인가요?",
        "mapping": "일반직원인원",
        "unit": "명",
        "validate_against": "headcount"
    },
    {
        "id": "q23",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "계약직 인원은 몇 명인가요?",
        "mapping": "계약직인원",
        "unit": "명",
        "validate_against": "headcount"
    },
    {
        "id": "q24",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "퇴직자 중 임원 인원은 몇 명인가요?",
        "mapping": "퇴직임원인원",
        "unit": "명",
        "validate_against": "headcount"
    },
    {
        "id": "q25",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "퇴직자 중 일반직원 인원은 몇 명인가요?",
        "mapping": "퇴직직원인원",
        "unit": "명",
        "validate_against": "headcount"
    },
    {
        "id": "q26",
        "type": "number",
        "category": "headcount_aggregates",
        "question": "퇴직자 중 계약직 인원은 몇 명인가요?",
        "mapping": "퇴직계약직인원",
        "unit": "명",
        "validate_against": "headcount"
    }
]


# ========== 금액 집계 질문 (q27-q30) ==========
AMOUNT_AGGREGATES = [
    {
        "id": "q27",
        "type": "number",
        "category": "amount_aggregates",
        "question": "현재 퇴직급여채무 합계는 얼마인가요?",
        "mapping": "퇴직금채무합계",
        "unit": "원",
        "validate_against": "amount",
        "format": "currency"
    },
    {
        "id": "q28",
        "type": "number",
        "category": "amount_aggregates",
        "question": "중간정산 합계는 얼마인가요?",
        "mapping": "중간정산합계",
        "unit": "원",
        "validate_against": "amount",
        "format": "currency"
    },
    {
        "id": "q29",
        "type": "number",
        "category": "amount_aggregates",
        "question": "DC전환금 합계는 얼마인가요?",
        "mapping": "DC전환합계",
        "unit": "원",
        "validate_against": "amount",
        "format": "currency"
    },
    {
        "id": "q30",
        "type": "number",
        "category": "amount_aggregates",
        "question": "기타 반환금 합계는 얼마인가요?",
        "mapping": "기타반환합계",
        "unit": "원",
        "validate_against": "amount",
        "format": "currency"
    }
]


# ========== 전체 질문 통합 ==========
ALL_QUESTIONS: List[Dict[str, Any]] = (
    BASIC_QUESTIONS +
    HEADCOUNT_AGGREGATES +
    AMOUNT_AGGREGATES
)


def get_questions_by_category(category: str) -> List[Dict[str, Any]]:
    """카테고리별 질문 필터링"""
    return [q for q in ALL_QUESTIONS if q.get("category") == category]


def get_validation_questions() -> List[Dict[str, Any]]:
    """Layer 2 검증이 필요한 질문만 반환 (aggregate 카테고리)"""
    return [q for q in ALL_QUESTIONS if q.get("validate_against")]


def get_question_by_id(question_id: str) -> Dict[str, Any]:
    """ID로 특정 질문 찾기"""
    for q in ALL_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


def format_question_for_chatbot(question: Dict[str, Any]) -> str:
    """챗봇용 질문 포맷팅"""
    q_text = question["question"]
    
    if question["type"] == "choice":
        choices_str = " / ".join(question["choices"])
        return f"{q_text} ({choices_str})"
    elif question["type"] == "number":
        unit = question.get("unit", "")
        return f"{q_text} {f'(단위: {unit})' if unit else ''}".strip()
    else:
        return q_text


# ========== 질문 요약 정보 ==========
QUESTION_SUMMARY = {
    "total": len(ALL_QUESTIONS),
    "categories": {
        "data_quality": len(BASIC_QUESTIONS),
        "headcount_aggregates": len(HEADCOUNT_AGGREGATES),
        "amount_aggregates": len(AMOUNT_AGGREGATES)
    }
}


if __name__ == "__main__":
    print("=== 진단 질문 시스템 ===\n")
    print(f"총 질문 수: {QUESTION_SUMMARY['total']}개")
    print(f"  - 기본 질문: {QUESTION_SUMMARY['categories']['data_quality']}개 (q1-q14)")
    print(f"  - 인원 집계: {QUESTION_SUMMARY['categories']['headcount_aggregates']}개 (q21-q24)")
    print(f"  - 금액 집계: {QUESTION_SUMMARY['categories']['amount_aggregates']}개 (q25-q28)")
    print("\n=== 검증 대상 질문 목록 ===")
    for q in get_validation_questions():
        print(f"{q['id']}: {q['question'][:50]}... → {q['validate_against']}")
