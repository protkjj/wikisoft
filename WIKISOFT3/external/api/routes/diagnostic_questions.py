from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/diagnostic-questions", tags=["diagnostic-questions"])


# 재직자 명부 검증용 13개 질문 (24개에서 축소)
# - 퇴직자 관련 제거 (재직자 명부만 받음)
# - 추계액 관련 제거 (계리 계산 불필요)
# - 재직자 인원은 유지 (누락/중복 검증용)
FIXED_QUESTIONS = [
    # 정책/제도 확인 (8개)
    {"id": "q1", "type": "choice", "category": "data_quality", "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?", "choices": ["예", "아니오"], "mapping": "사외적립자산"},
    {"id": "q2", "type": "choice", "category": "data_quality", "question": "정년 - 정년은 만 60 세 입니까?", "choices": ["예", "아니오"], "mapping": "정년"},
    {"id": "q3", "type": "choice", "category": "data_quality", "question": "임금피크제 - 임금피크제 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "임금피크제"},
    {"id": "q4", "type": "choice", "category": "data_quality", "question": "기타장기종업원급여 - 기타장기종업원급여 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "기타장기급여"},
    {"id": "q6", "type": "choice", "category": "data_quality", "question": "연봉제/호봉제 - 근무기간에 따른 호봉 미적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "급여체계"},
    {"id": "q7", "type": "choice", "category": "data_quality", "question": "채권 등급 - 할인율 산출기준 채권 회사채 AA++ 적용 기업입니까?", "choices": ["예", "아니오"], "mapping": "할인율기준"},
    {"id": "q8", "type": "choice", "category": "data_quality", "question": "1년 미만 재직자 - 1년 미만 재직자도 기재 하셨습니까?", "choices": ["예", "아니오"], "mapping": "1년미만재직자"},
    
    # 데이터 품질 확인 (3개)
    {"id": "q10", "type": "choice", "category": "data_quality", "question": "기준급여 - 3개월 미만 재직자의 경우 한달 근무 시 지급받는 급여로 기재하셨습니까?", "choices": ["예", "아니오"], "mapping": "기준급여"},
    {"id": "q12", "type": "choice", "category": "data_quality", "question": "재직자명부 - 평가기준일 퇴사자를 제외 하셨습니까?", "choices": ["예", "아니오"], "mapping": "재직자명부퇴사자제외"},
    {"id": "q13", "type": "choice", "category": "data_quality", "question": "중간정산 - 근퇴법 시행령 제3조에 해당합니까?", "choices": ["예", "아니오"], "mapping": "중간정산사유"},
    
    # 재직자 인원 집계 (3개 - 누락/중복 검증용)
    {"id": "q21", "type": "number", "category": "headcount_aggregates", "question": "임원 인원은 몇 명인가요?", "mapping": "임원인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=3"},
    {"id": "q22", "type": "number", "category": "headcount_aggregates", "question": "일반직원 인원은 몇 명인가요?", "mapping": "일반직원인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=1"},
    {"id": "q23", "type": "number", "category": "headcount_aggregates", "question": "계약직 인원은 몇 명인가요?", "mapping": "계약직인원", "unit": "명", "validate_against": "headcount", "suggest_from": "종업원구분=4"},
]


@router.get("")
async def list_questions() -> dict:
    """재직자 명부 검증용 13개 질문 반환.
    
    - 퇴직자/추계액 관련 제거 (재직자 명부만 검증)
    - 재직자 인원(q21-23)은 유지 (누락/중복 검증용)
    """
    return {
        "total": len(FIXED_QUESTIONS),
        "questions": FIXED_QUESTIONS,
        "note": "재직자 명부 검증용 13개 질문 (퇴직자/추계액 제외)",
    }


@router.post("/dynamic")
async def generate_dynamic_questions(
    anomalies: Optional[dict] = None,
    matches: Optional[dict] = None,
    validation: Optional[dict] = None
) -> dict:
    """
    검증 결과를 기반으로 동적 질문 생성
    
    이상치 감지 결과에 따라 추가 확인이 필요한 질문을 자동 생성합니다.
    """
    from internal.ai.dynamic_questions import generate_dynamic_questions, format_questions_for_ui
    
    questions = generate_dynamic_questions(
        anomalies=anomalies or {},
        matches=matches or {},
        validation=validation or {},
        max_questions=5
    )
    
    return {
        "total": len(questions),
        "questions": format_questions_for_ui(questions),
        "note": "검증 결과 기반 동적 생성 질문"
    }
