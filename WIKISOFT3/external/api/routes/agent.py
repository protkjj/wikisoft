import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from internal.agent.tool_registry import get_registry
from internal.ai.diagnostic_questions import ALL_QUESTIONS
from internal.ai.llm_client import get_llm_client

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
    system_prompt = (
        "You are the WIKISOFT3 validation co-pilot. "
        "Help users validate HR/pension Excel files. "
        "Use tools when needed. Be concise in Korean."
    )

    user_content = req.message.strip()
    if req.context:
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

        return {
            "answer": answer,
            "provider": client.provider,
            "used_tools": [tc["function"]["name"] for tc in tool_calls],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"agent error: {str(e)}")
