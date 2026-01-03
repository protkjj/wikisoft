"""
학습 API: 사용자 피드백으로부터 규칙 학습
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

from external.api.auth import verify_token
from internal.ai.knowledge_base import (
    add_error_rule,
    learn_from_correction,
    load_error_rules,
    remove_error_rule
)
from internal.ai.autonomous_learning import (
    get_learning_stats,
    analyze_and_learn
)

router = APIRouter(prefix="/api/learn", tags=["learn"])


class ErrorCorrectionRequest(BaseModel):
    """사용자가 오류를 수정했을 때"""
    field: str
    original_value: str
    was_error: bool  # AI가 오류라고 했는지
    is_actually_error: bool  # 실제로 오류인지 (사용자 판단)
    reason: Optional[str] = None  # 사용자 설명
    diagnostic_context: Optional[Dict[str, Any]] = None


class NewRuleRequest(BaseModel):
    """새 규칙 직접 추가"""
    field: str
    condition: str
    message: str
    severity: str = "error"
    category: str = "user_defined"
    context_override: Optional[Dict[str, str]] = None


@router.post("/correction")
async def learn_correction(
    request: ErrorCorrectionRequest,
    token: str = Depends(verify_token)
) -> dict:
    """
    사용자가 AI 판단을 수정했을 때 학습.
    
    예: AI가 "65세 입사"를 오류라고 했는데, 
        사용자가 "임원이라 정상"이라고 수정
    """
    # AI가 틀렸을 경우에만 학습
    if request.was_error != request.is_actually_error:
        interpretation = request.reason or (
            "오류 아님" if not request.is_actually_error else "오류임"
        )
        
        result = learn_from_correction(
            field=request.field,
            original_value=request.original_value,
            was_error=request.was_error,
            correct_interpretation=interpretation,
            diagnostic_context=request.diagnostic_context
        )
        
        return {
            "status": "learned",
            "message": result,
            "ai_was_wrong": True
        }
    
    return {
        "status": "no_change",
        "message": "AI 판단이 맞았으므로 학습 불필요",
        "ai_was_wrong": False
    }


@router.post("/rule")
async def add_rule(
    request: NewRuleRequest,
    token: str = Depends(verify_token)
) -> dict:
    """새 규칙 직접 추가"""
    rule_id = add_error_rule(
        field=request.field,
        condition=request.condition,
        message=request.message,
        severity=request.severity,
        category=request.category,
        context_override=request.context_override
    )
    
    return {
        "status": "added",
        "rule_id": rule_id,
        "message": f"규칙 {rule_id} 추가됨"
    }


@router.get("/rules")
async def get_rules() -> dict:
    """현재 규칙 목록 조회"""
    rules = load_error_rules()
    
    # 카테고리별 그룹화
    by_category = {}
    for rule in rules:
        cat = rule.get("category", "기타")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(rule)
    
    return {
        "total": len(rules),
        "by_category": by_category,
        "rules": rules
    }


@router.delete("/rule/{rule_id}")
async def delete_rule(
    rule_id: str,
    token: str = Depends(verify_token)
) -> dict:
    """규칙 삭제"""
    success = remove_error_rule(rule_id)
    
    if success:
        return {"status": "deleted", "rule_id": rule_id}
    else:
        return {"status": "not_found", "rule_id": rule_id}


@router.post("/batch-correction")
async def batch_learn(
    corrections: List[ErrorCorrectionRequest],
    token: str = Depends(verify_token)
) -> dict:
    """여러 수정 한번에 학습"""
    learned_count = 0
    
    for c in corrections:
        if c.was_error != c.is_actually_error:
            learn_from_correction(
                field=c.field,
                original_value=c.original_value,
                was_error=c.was_error,
                correct_interpretation=c.reason or "사용자 수정",
                diagnostic_context=c.diagnostic_context
            )
            learned_count += 1
    
    return {
        "status": "ok",
        "total": len(corrections),
        "learned": learned_count
    }


@router.get("/autonomous/stats")
async def get_autonomous_stats() -> dict:
    """자율 학습 통계 조회"""
    return get_learning_stats()


@router.post("/autonomous/analyze")
async def trigger_analysis(
    token: str = Depends(verify_token)
) -> dict:
    """수동으로 자율 학습 분석 트리거"""
    result = analyze_and_learn()
    return {
        "status": "analyzed",
        "result": result
    }
