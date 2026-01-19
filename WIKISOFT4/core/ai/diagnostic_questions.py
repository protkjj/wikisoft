"""
진단 질문 시스템 (24개) - v2 이식
"""
from typing import List, Dict, Any

# 기본 14개 질문
BASIC_QUESTIONS = [
    {"id": "q1", "type": "choice", "category": "data_quality", "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?", "choices": ["예", "아니오"], "mapping": "사외적립자산"},
    {"id": "q2", "type": "choice", "category": "data_quality", "question": "정년 - 정년은 만 60 세 입니까?", "choices": ["예", "아니오"], "mapping": "정년"},
    {"id": "q3", "type": "choice", "category": "data_quality", "question": "임금피크제 - 임금피크제 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "임금피크제"},
    {"id": "q4", "type": "choice", "category": "data_quality", "question": "기타장기종업원급여 - 기타장기종업원급여 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "기타장기급여"},
    {"id": "q6", "type": "choice", "category": "data_quality", "question": "연봉제/호봉제 - 근무기간에 따른 호봉 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "급여체계"},
    {"id": "q7", "type": "choice", "category": "data_quality", "question": "채권 등급 - 할인율 산출기준 채권 회사채 AA++ 적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "할인율기준"},
    {"id": "q8", "type": "choice", "category": "data_quality", "question": "1년 미만 재직자 - 1년 미만 재직자도 기재 하셨습니까?", "choices": ["예", "아니오"], "mapping": "1년미만재직자"},
    {"id": "q9", "type": "choice", "category": "data_quality", "question": "퇴직금 추계액 - 모든 재직자의 당년도, 차년도 퇴직금 추계액을 입력하셨습니까?", "choices": ["예", "아니오"], "mapping": "퇴직금추계액"},
    {"id": "q10", "type": "choice", "category": "data_quality", "question": "기준급여 - 3개월 미만 재직자의 경우 한달 근무 시 지급받는 급여로 기재하셨습니까?", "choices": ["예", "아니오"], "mapping": "기준급여"},
    {"id": "q11", "type": "choice", "category": "data_quality", "question": "평가기준일 퇴사자 - 평가기준일 발생 퇴직금을 비용 처리 하셨습니까?", "choices": ["예", "아니오"], "mapping": "평가기준일퇴사자비용"},
    {"id": "q12", "type": "choice", "category": "data_quality", "question": "재직자명부 - 평가기준일 퇴사자를 제외 하셨습니까?", "choices": ["예", "아니오"], "mapping": "재직자명부퇴사자제외"},
    {"id": "q13", "type": "choice", "category": "data_quality", "question": "중간정산 - 근퇴법 시행령 제3조에 해당합니까?", "choices": ["예", "아니오"], "mapping": "중간정산사유"},
    {"id": "q14", "type": "choice", "category": "data_quality", "question": "퇴직자명부 - 평가기준일 퇴사자를 포함하셨습니까?", "choices": ["예", "아니오"], "mapping": "퇴직자명부포함"},
]

# 인원 집계 (프론트엔드 질문 ID 기준 - compat.py ROSTER_QUESTIONS와 일치)
HEADCOUNT_AGGREGATES = [
    {"id": "2-a.1", "type": "number", "category": "headcount_aggregates", "question": "재직자수 - 임원", "mapping": "재직자수_임원", "unit": "명", "validate_against": "headcount"},
    {"id": "2-a.2", "type": "number", "category": "headcount_aggregates", "question": "재직자수 - 직원", "mapping": "재직자수_직원", "unit": "명", "validate_against": "headcount"},
    {"id": "2-a.3", "type": "number", "category": "headcount_aggregates", "question": "재직자수 - 계약직", "mapping": "재직자수_계약직", "unit": "명", "validate_against": "headcount"},
    {"id": "2-b.1", "type": "number", "category": "headcount_aggregates", "question": "퇴직자수 - 임원", "mapping": "퇴직자수_임원", "unit": "명"},
    {"id": "2-b.2", "type": "number", "category": "headcount_aggregates", "question": "퇴직자수 - 직원", "mapping": "퇴직자수_직원", "unit": "명"},
    {"id": "2-b.3", "type": "number", "category": "headcount_aggregates", "question": "퇴직자수 - 계약직", "mapping": "퇴직자수_계약직", "unit": "명"},
]

# 금액 집계 (프론트엔드 질문 ID 기준 - compat.py ROSTER_QUESTIONS와 일치)
AMOUNT_AGGREGATES = [
    {"id": "2-d", "type": "number", "category": "amount_aggregates", "question": "퇴직금 추계액 합계", "mapping": "퇴직금추계액합계", "unit": "원", "validate_against": "amount", "format": "currency"},
    {"id": "2-e.A.2", "type": "number", "category": "amount_aggregates", "question": "중간정산금액", "mapping": "중간정산합계", "unit": "원", "validate_against": "amount", "format": "currency"},
    {"id": "2-e.A.3", "type": "number", "category": "amount_aggregates", "question": "DC전환금", "mapping": "DC전환합계", "unit": "원", "validate_against": "amount", "format": "currency"},
]

ALL_QUESTIONS: List[Dict[str, Any]] = BASIC_QUESTIONS + HEADCOUNT_AGGREGATES + AMOUNT_AGGREGATES


def get_questions_by_category(category: str) -> List[Dict[str, Any]]:
    return [q for q in ALL_QUESTIONS if q.get("category") == category]


def get_validation_questions() -> List[Dict[str, Any]]:
    return [q for q in ALL_QUESTIONS if q.get("validate_against")]


def get_question_by_id(question_id: str) -> Dict[str, Any]:
    for q in ALL_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


def format_question_for_chatbot(question: Dict[str, Any]) -> str:
    q_text = question["question"]
    if question["type"] == "choice":
        choices_str = " / ".join(question["choices"])
        return f"{q_text} ({choices_str})"
    if question["type"] == "number":
        unit = question.get("unit", "")
        return f"{q_text} {f'(단위: {unit})' if unit else ''}".strip()
    return q_text


QUESTION_SUMMARY = {
    "total": len(ALL_QUESTIONS),
    "categories": {
        "data_quality": len(BASIC_QUESTIONS),
        "headcount_aggregates": len(HEADCOUNT_AGGREGATES),
        "amount_aggregates": len(AMOUNT_AGGREGATES),
    },
}


# 재직자 명부 검증용 질문 ID (퇴직자/추계액 제외)
# 프론트엔드 질문 ID 기준 (compat.py ROSTER_QUESTIONS와 일치)
ROSTER_QUESTION_IDS = [
    "q1", "q2", "q3", "q4", "q6", "q7", "q8",  # 정책/제도 7개
    "q10", "q12", "q13",  # 데이터 품질 3개
    "2-a.1", "2-a.2", "2-a.3",  # 인원 집계 3개 (재직자수: 임원/직원/계약직)
]


def get_roster_questions() -> List[Dict[str, Any]]:
    """재직자 명부 검증용 13개 질문만 반환 (Single Source of Truth)"""
    return [q for q in ALL_QUESTIONS if q["id"] in ROSTER_QUESTION_IDS]


def format_answers_for_ai(answers: Dict[str, Any]) -> str:
    """진단 답변을 AI가 이해하기 쉬운 형태로 포맷팅 (공통 함수)"""
    lines = []
    for qid, value in answers.items():
        question = get_question_by_id(qid)
        if question:
            # 질문 텍스트에서 앞부분(카테고리)만 추출
            q_text = question["question"]
            # "사외적립자산 - 회계 장부..." → "사외적립자산"
            label = q_text.split(" - ")[0] if " - " in q_text else q_text[:20]
        else:
            label = qid
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)
