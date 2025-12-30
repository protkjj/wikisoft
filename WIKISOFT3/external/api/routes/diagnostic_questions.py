from fastapi import APIRouter

router = APIRouter(prefix="/diagnostic-questions", tags=["diagnostic-questions"])


# v2에서 사용한 24개 고정 질문 (그대로 유지)
# AI가 기본값을 제안하되, 사용자가 확인/수정 필수
FIXED_QUESTIONS = [
    # 기본 14개 (정책/데이터 확인)
    {"id": "q1", "type": "choice", "category": "data_quality", "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?", "choices": ["예", "아니오"], "mapping": "사외적립자산"},
    {"id": "q2", "type": "choice", "category": "data_quality", "question": "정년 - 정년은 만 60 세 입니까?", "choices": ["예", "아니오"], "mapping": "정년"},
    {"id": "q3", "type": "choice", "category": "data_quality", "question": "임금피크제 - 임금피크제 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "임금피크제"},
    {"id": "q4", "type": "choice", "category": "data_quality", "question": "기타장기종업원급여 - 기타장기종업원급여 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "기타장기급여"},
    {"id": "q5", "type": "choice", "category": "data_quality", "question": "퇴직금제도 - 퇴직금제도는 법정제를 적용합니까?", "choices": ["예", "아니오"], "mapping": "퇴직금제도"},
    {"id": "q6", "type": "choice", "category": "data_quality", "question": "연봉제/호봉제 - 근무기간에 따른 호봉 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "급여체계"},
    {"id": "q7", "type": "choice", "category": "data_quality", "question": "채권 등급 - 할인율 산출기준 채권 회사채 AA++ 적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "할인율기준"},
    {"id": "q8", "type": "choice", "category": "data_quality", "question": "1년 미만 재직자 - 1년 미만 재직자도 기재 하셨습니까?", "choices": ["예", "아니오"], "mapping": "1년미만재직자"},
    {"id": "q9", "type": "choice", "category": "data_quality", "question": "퇴직금 추계액 - 모든 재직자의 당년도, 차년도 퇴직금 추계액을 입력하셨습니까?", "choices": ["예", "아니오"], "mapping": "퇴직금추계액"},
    {"id": "q10", "type": "choice", "category": "data_quality", "question": "기준급여 - 3개월 미만 재직자의 경우 한달 근무 시 지급받는 급여로 기재하셨습니까?", "choices": ["예", "아니오"], "mapping": "기준급여"},
    {"id": "q11", "type": "choice", "category": "data_quality", "question": "평가기준일 퇴사자 - 평가기준일 발생 퇴직금을 비용 처리 하셨습니까?", "choices": ["예", "아니오"], "mapping": "평가기준일퇴사자비용"},
    {"id": "q12", "type": "choice", "category": "data_quality", "question": "재직자명부 - 평가기준일 퇴사자를 제외 하셨습니까?", "choices": ["예", "아니오"], "mapping": "재직자명부퇴사자제외"},
    {"id": "q13", "type": "choice", "category": "data_quality", "question": "중간정산 - 근퇴법 시행령 제3조에 해당합니까?", "choices": ["예", "아니오"], "mapping": "중간정산사유"},
    {"id": "q14", "type": "choice", "category": "data_quality", "question": "퇴직자명부 - 평가기준일 퇴사자를 포함하셨습니까?", "choices": ["예", "아니오"], "mapping": "퇴직자명부포함"},
    # 인원 집계 6개 (AI가 기본값 제안, 사용자 확인)
    {"id": "q21", "type": "number", "category": "headcount_aggregates", "question": "임원 인원은 몇 명인가요?", "mapping": "임원인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=3"},
    {"id": "q22", "type": "number", "category": "headcount_aggregates", "question": "일반직원 인원은 몇 명인가요?", "mapping": "일반직원인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=1"},
    {"id": "q23", "type": "number", "category": "headcount_aggregates", "question": "계약직 인원은 몇 명인가요?", "mapping": "계약직인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=4"},
    {"id": "q24", "type": "number", "category": "headcount_aggregates", "question": "퇴직자 중 임원 인원은 몇 명인가요?", "mapping": "퇴직임원인원", "unit": "명", "validate_against": "headcount"},
    {"id": "q25", "type": "number", "category": "headcount_aggregates", "question": "퇴직자 중 일반직원 인원은 몇 명인가요?", "mapping": "퇴직직원인원", "unit": "명", "validate_against": "headcount"},
    {"id": "q26", "type": "number", "category": "headcount_aggregates", "question": "퇴직자 중 계약직 인원은 몇 명인가요?", "mapping": "퇴직계약직인원", "unit": "명", "validate_against": "headcount"},
    # 금액 집계 4개 (AI가 기본값 제안, 사용자 확인)
    {"id": "q27", "type": "number", "category": "amount_aggregates", "question": "현재 퇴직급여채무 합계는 얼마인가요?", "mapping": "퇴직금채무합계", "unit": "원", "validate_against": "amount", "format": "currency", "suggest_from": "당년도퇴직금추계액.sum()"},
    {"id": "q28", "type": "number", "category": "amount_aggregates", "question": "중간정산 합계는 얼마인가요?", "mapping": "중간정산합계", "unit": "원", "validate_against": "amount", "format": "currency", "suggest_from": "중간정산액.sum()"},
    {"id": "q29", "type": "number", "category": "amount_aggregates", "question": "DC전환금 합계는 얼마인가요?", "mapping": "DC전환합계", "unit": "원", "validate_against": "amount", "format": "currency"},
    {"id": "q30", "type": "number", "category": "amount_aggregates", "question": "기타 반환금 합계는 얼마인가요?", "mapping": "기타반환합계", "unit": "원", "validate_against": "amount", "format": "currency"},
]


@router.get("")
async def list_questions() -> dict:
    """24개 고정 질문 반환.
    
    AI가 기본값을 제안하지만, 사용자가 반드시 확인/수정해야 함.
    (중복/누락 검증을 위해 24개 모두 유지)
    """
    return {
        "total": len(FIXED_QUESTIONS),
        "questions": FIXED_QUESTIONS,
        "note": "24개 고정 질문. AI가 기본값 제안하지만 사용자 확인 필수 (중복/누락 검증용)",
    }
