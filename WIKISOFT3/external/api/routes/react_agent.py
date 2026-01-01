"""
ReACT Agent API Routes

ReACT 에이전트 기반 검증 API.
- Think → Act → Observe 루프
- 자율적 의사결정
- 추론 과정 투명화
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from typing import Optional
import json

from internal.agent.tool_registry import get_registry
from internal.agent.react_agent import create_react_agent
from internal.memory.case_store import get_case_store, save_successful_case
from internal.utils.security import secure_logger

router = APIRouter(prefix="/react-agent", tags=["react-agent"])


@router.post("/validate")
async def react_validate(
    file: UploadFile = File(...),
    chatbot_answers: Optional[str] = Form(None),
    verbose: Optional[bool] = Form(False)
) -> dict:
    """
    ReACT 에이전트 기반 파일 검증.
    
    기존 파이프라인과 달리:
    - 에이전트가 스스로 다음 액션 결정
    - 신뢰도 낮으면 자동 재시도
    - 추론 과정 기록 및 반환
    
    Args:
        file: 검증할 Excel/CSV 파일
        chatbot_answers: 진단 질문 답변 (JSON 문자열)
        verbose: 상세 로그 출력 여부
    
    Returns:
        검증 결과 + 에이전트 추론 히스토리
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is required")
    
    # 진단 답변 파싱
    diagnostic_answers = {}
    if chatbot_answers:
        try:
            diagnostic_answers = json.loads(chatbot_answers)
        except json.JSONDecodeError:
            pass
    
    file_bytes = await file.read()
    registry = get_registry()
    
    # ReACT 에이전트 생성 및 실행
    agent = create_react_agent(
        tool_registry=registry,
        verbose=verbose
    )
    
    result = agent.run(
        file_bytes=file_bytes,
        diagnostic_answers=diagnostic_answers,
        sheet_type="재직자"
    )
    
    # 추론 과정 설명 추가
    result["reasoning_explanation"] = agent.explain_reasoning()
    
    # 성공 케이스 저장
    if result.get("confidence", {}).get("score", 0) >= 0.8:
        try:
            headers = result.get("steps", {}).get("parsed_summary", {}).get("headers", [])
            matches = result.get("steps", {}).get("matches", {}).get("matches", [])
            save_successful_case(
                headers=headers,
                matches=matches,
                confidence=result.get("confidence", {}).get("score", 0),
                was_auto_approved=True,
                metadata={"filename": file.filename, "agent": "react"}
            )
        except Exception as e:
            secure_logger.error(f"케이스 저장 실패: {e}")
    
    return result


@router.get("/stats")
async def get_agent_stats() -> dict:
    """
    에이전트 학습 통계.
    
    Returns:
        케이스 저장소 통계 (총 케이스 수, 자동 승인율 등)
    """
    store = get_case_store()
    return {
        "case_store": store.get_stats(),
        "agent_info": {
            "type": "ReACT",
            "max_iterations": 5,
            "confidence_thresholds": {
                "auto_complete": 0.95,
                "auto_correct": 0.80,
                "needs_review": 0.50,
            }
        }
    }


@router.post("/save-correction")
async def save_manual_correction(
    headers: str = Form(...),
    original_matches: str = Form(...),
    human_corrections: str = Form(...),
    metadata: Optional[str] = Form(None)
) -> dict:
    """
    수동 수정 케이스 저장.
    
    사용자가 매칭을 수정한 경우, 그 수정 내역을 저장하여
    향후 Few-shot Learning에 활용.
    
    Args:
        headers: 원본 헤더 (JSON 배열)
        original_matches: 원래 AI 매칭 결과 (JSON 배열)
        human_corrections: 사람이 수정한 매핑 (JSON 객체 {"원본헤더": "수정된_필드"})
        metadata: 추가 메타데이터 (JSON 객체)
    
    Returns:
        저장된 케이스 ID
    """
    try:
        headers_list = json.loads(headers)
        matches_list = json.loads(original_matches)
        corrections_dict = json.loads(human_corrections)
        meta = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON 파싱 오류: {e}"
        )
    
    case_id = save_successful_case(
        headers=headers_list,
        matches=matches_list,
        confidence=0.0,  # 사람이 수정했으므로 원래 신뢰도는 0
        was_auto_approved=False,
        human_corrections=corrections_dict,
        metadata={**meta, "correction_type": "manual"}
    )
    
    return {
        "status": "saved",
        "case_id": case_id,
        "message": "수정 내역이 저장되었습니다. 향후 매칭 정확도 향상에 활용됩니다."
    }
