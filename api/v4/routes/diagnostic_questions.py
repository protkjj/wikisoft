from fastapi import APIRouter
from typing import Optional

from core.ai.diagnostic_questions import get_roster_questions

router = APIRouter(prefix="/api/diagnostic-questions", tags=["diagnostic-questions"])


@router.get("")
async def list_questions() -> dict:
    """재직자 명부 검증용 13개 질문 반환.
    
    - 퇴직자/추계액 관련 제거 (재직자 명부만 검증)
    - 재직자 인원(q21-23)은 유지 (누락/중복 검증용)
    - Single Source of Truth: internal/ai/diagnostic_questions.py
    """
    questions = get_roster_questions()
    return {
        "total": len(questions),
        "questions": questions,
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
    from core.ai.dynamic_questions import generate_dynamic_questions, format_questions_for_ui
    
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
