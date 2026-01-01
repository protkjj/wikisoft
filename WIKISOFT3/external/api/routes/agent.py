import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from internal.agent.tool_registry import get_registry
from internal.ai.diagnostic_questions import ALL_QUESTIONS
from internal.ai.knowledge_base import get_system_context
from internal.ai.llm_client import get_llm_client
from internal.ai.autonomous_learning import analyze_chat_for_learning

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentAskRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# 툴 정의 (OpenAI function calling 형식)
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_diagnostic_questions",
            "description": "재직자 명부 검증용 13개 진단 질문 목록을 조회합니다.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_tools",
            "description": "시스템에서 사용 가능한 검증 도구 목록을 조회합니다 (파싱, 매칭, 검증, 리포트 생성 등).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """툴 실행 함수"""
    if tool_name == "list_diagnostic_questions":
        return {
            "total": len(ALL_QUESTIONS),
            "questions": [
                {"id": q["id"], "question": q["question"], "type": q["type"]}
                for q in ALL_QUESTIONS[:5]  # 처음 5개만 반환 (토큰 절약)
            ],
            "note": "총 13개 질문 중 처음 5개만 표시",
        }
    elif tool_name == "list_available_tools":
        registry = get_registry()
        return {"tools": registry.list_tools()}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def _build_messages(req: AgentAskRequest) -> List[Dict[str, str]]:
    # 시스템 지식 로드
    knowledge = get_system_context(req.message)
    
    # 컨텍스트가 있으면 파일이 이미 업로드된 상태
    has_context = req.context and req.context.get("has_file")
    
    context_info = ""
    if has_context and req.context.get("validation_results"):
        vr = req.context["validation_results"]
        
        # 매칭 결과 요약
        matches = vr.get("steps", {}).get("matches", {}).get("matches", [])
        matched_fields = [m.get("target") for m in matches if m.get("target")]
        required_fields = ['사원번호', '생년월일', '성별', '입사일자', '종업원구분', '기준급여']
        matched_required = [f for f in required_fields if f in matched_fields]
        missing_required = [f for f in required_fields if f not in matched_fields]
        
        # 검증 오류/경고 요약
        errors = vr.get("steps", {}).get("validation", {}).get("errors", [])
        warnings = vr.get("steps", {}).get("validation", {}).get("warnings", [])
        
        # 신뢰도
        confidence = vr.get("confidence", {}).get("score", 0)
        
        context_info = f"""
=== 현재 검증 완료된 파일 상태 ===
✅ 파일이 정상적으로 업로드되어 검증 완료됨

📊 컬럼 매핑 결과:
- 매핑된 필드 {len(matched_fields)}개: {', '.join(matched_fields)}
- 필수 필드 매핑: {', '.join(matched_required)} ({len(matched_required)}/{len(required_fields)}개 완료)
- 누락된 필수 필드: {', '.join(missing_required) if missing_required else '없음 (모두 매핑됨)'}

🔍 검증 결과:
- 신뢰도: {confidence*100:.0f}%
- 오류: {len(errors)}건
- 경고: {len(warnings)}건
{('- 오류 내용: ' + ', '.join([e.get('message', '')[:50] for e in errors[:3]])) if errors else ''}
{('- 경고 내용: ' + ', '.join([w.get('message', '')[:50] for w in warnings[:3]])) if warnings else ''}

⚠️ 주의: 위 정보가 이미 검증된 결과입니다. 사용자에게 "파일을 제공해주세요"라고 하지 마세요.
"""

    system_prompt = f"""You are the WIKISOFT3 validation co-pilot.
Help users validate HR/pension Excel files.
Use tools when needed. Be concise in Korean.

=== System Knowledge ===
{knowledge}

{context_info}

⚠️ 중요 지침:
1. 사용자가 이미 파일을 업로드했으면 "파일을 제공해 주세요" 같은 말 금지
2. 날짜/숫자 형식은 시스템이 자동 변환하므로 "형식 확인" 요청 금지
3. 검증 결과가 context에 있으면 그걸 바탕으로 바로 답변
4. 실제 데이터 값 언급 시 개인정보 마스킹 (예: 사원번호 앞 4자리만)

When answering questions about the system, refer to this knowledge base."""

    user_content = req.message.strip()
    if req.context and not has_context:
        user_content += f"\n\nContext: {json.dumps(req.context, ensure_ascii=False)}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


@router.post("/ask")
async def ask_agent(req: AgentAskRequest) -> Dict[str, Any]:
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required")

    try:
        client = get_llm_client()
    except ValueError as e:
        # API 키가 없는 경우 친절한 메시지 반환
        return {
            "answer": "⚠️ AI 기능을 사용하려면 OpenAI API 키가 필요합니다.\n\n설정 방법:\n1. `.env` 파일에 `OPENAI_API_KEY=sk-...` 추가\n2. 또는 환경변수로 설정\n\n현재는 AI 없이 기본 검증 기능만 사용 가능합니다.",
            "provider": "none",
            "used_tools": [],
            "error": "no_api_key"
        }
    
    try:
        messages = _build_messages(req)

        # 1차 LLM 호출 (툴 사용 가능)
        response = client.chat_with_tools(messages, AGENT_TOOLS)

        # 툴 호출이 있으면 실행 후 2차 호출
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            # 툴 실행
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                tool_result = _execute_tool(tool_name, arguments)

                # 툴 결과를 메시지에 추가
                messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

            # 2차 LLM 호출 (툴 결과 포함)
            final_response = client.chat_with_tools(messages, AGENT_TOOLS)
            answer = final_response.get("content", "")
        else:
            answer = response.get("content", "")

        # 자율 학습: 대화 내용 분석하여 학습 기회 감지
        try:
            validation_context = req.context.get("validation_results") if req.context else None
            analyze_chat_for_learning(req.message, answer, validation_context)
        except Exception as learn_err:
            # 학습 실패해도 응답은 정상적으로 반환
            logger.warning(f"Autonomous Learning 분석 실패: {learn_err}")

        return {
            "answer": answer,
            "provider": client.provider,
            "used_tools": [tc["function"]["name"] for tc in tool_calls],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"agent error: {str(e)}")


# ============================================
# /chat 엔드포인트 - SheetEditor AI 챗봇용
# ============================================

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


@router.post("/chat", summary="SheetEditor AI 챗봇")
async def chat_with_ai(req: ChatRequest):
    """
    SheetEditor의 AI 챗봇용 간단한 채팅 엔드포인트.
    사용자가 "수정해줘"라고 하면 [수정:행:필드:값] 형식으로 응답.
    """
    client = get_llm_client()
    
    system_prompt = """당신은 HR 데이터 수정 AI입니다.

[절대 규칙 - 반드시 지켜야 함]
수정 요청 시 응답에 반드시 이 형식 포함: [수정:행번호:필드명:새값]

예시:
- 사용자: "1번 2024년 1월 1일로 수정"
- 응답: 1번 항목을 수정합니다. [수정:15:입사일자:2024-01-01]

값 변환:
- 날짜: YYYY-MM-DD (2024년 1월 1일 → 2024-01-01)
- 금액: 숫자만 (206만원 → 2060000)

[수정:행:필드:값] 없이 응답하면 수정이 적용되지 않습니다!
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    if req.context:
        messages.append({"role": "system", "content": f"[컨텍스트]\n{req.context}"})
    
    messages.append({"role": "user", "content": req.message})
    
    try:
        response = client.chat(messages)
        answer = response.get("content", "") if isinstance(response, dict) else str(response)
        
        return {"response": answer}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": f"오류가 발생했습니다: {str(e)}"}
