"""
WIKISOFT3 호환 라우트

프론트엔드가 기존 /api/* 경로를 사용하므로 호환성을 위해 제공
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/diagnostic-questions")
async def get_diagnostic_questions():
    """진단 질문 목록 (WIKISOFT3 호환)"""
    return {
        "total": 13,
        "questions": [
            {"id": "q1", "type": "choice", "category": "data_quality",
             "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?",
             "choices": ["예", "아니오"], "mapping": "사외적립자산"},
            {"id": "q2", "type": "choice", "category": "data_quality",
             "question": "정년 - 정년은 만 60세 입니까?",
             "choices": ["예", "아니오"], "mapping": "정년"},
            {"id": "q3", "type": "choice", "category": "data_quality",
             "question": "임금피크제 - 임금피크제 미적용 기업입니까?",
             "choices": ["예", "아니오"], "mapping": "임금피크제"},
        ],
        "note": "WIKISOFT4 호환 모드 - 전체 질문은 추후 마이그레이션 예정"
    }


@router.get("/api/windmill/latest")
async def get_windmill_latest(limit: int = 5):
    """최근 실행 기록 (WIKISOFT3 호환)"""
    return {
        "runs": [],
        "note": "WIKISOFT4에서는 n8n/Temporal 워크플로우 사용 예정"
    }


@router.get("/api/health")
async def health_compat():
    """헬스 체크 (WIKISOFT3 호환)"""
    return {
        "status": "ok",
        "version": "4.1.0",
        "mode": "compatibility"
    }
