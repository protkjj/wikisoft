from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from internal.ai.llm_client import get_llm_client

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentAskRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def _build_messages(req: AgentAskRequest) -> list:
    system_prompt = (
        "You are the WIKISOFT3 validation co-pilot. "
        "Be concise. If you need data you do not have, say what is missing. "
        "If asked for actions, only describe what to do; do not fabricate results."
    )

    user_content = req.message.strip()
    if req.context:
        user_content += "\n\nContext:" + str(req.context)

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
        answer = client.chat(messages)
        return {"answer": answer, "provider": client.provider}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"agent error: {str(e)}")
