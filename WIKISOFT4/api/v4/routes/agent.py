"""
Agent Chat API - AI 어시스턴트 채팅 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import re

router = APIRouter(prefix="/api", tags=["Agent"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


def call_openai(system_prompt: str, user_message: str) -> str:
    """OpenAI API 호출"""
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"AI 응답 생성 실패: {str(e)}"


@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    AI 어시스턴트와 채팅

    - message: 사용자 메시지
    - context: 현재 데이터 컨텍스트 (오류 목록, 시트 데이터 등)
    """
    system_prompt = """당신은 퇴직연금 명부 데이터 검증을 돕는 AI 어시스턴트입니다.

## 역할
- 사용자가 데이터 오류를 수정하도록 도와줍니다
- 오류의 원인을 설명합니다
- 올바른 값을 제안합니다

## 수정 명령 형식
데이터를 수정할 때는 반드시 다음 형식을 사용하세요:
[수정:행번호:필드명:새값]

예시:
- [수정:3:입사일:2020-05-15]
- [수정:5:급여:3500000]
- [수정:7:성명:홍길동]

## 규칙
1. 날짜는 YYYY-MM-DD 형식 (예: 2024-05-20)
2. 금액은 숫자만 (예: 2060000)
3. 여러 셀을 수정할 때는 각각 별도의 [수정:...] 태그 사용
4. 수정 명령 없이 설명만 하면 실제 수정이 적용되지 않습니다

## 응답 스타일
- 간결하고 명확하게
- 한국어로 응답
- 수정 후 확인 메시지 포함
"""

    user_message = request.message
    if request.context:
        user_message = f"## 현재 데이터 상황\n{request.context}\n\n## 사용자 요청\n{request.message}"

    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        # API 키 없으면 간단한 규칙 기반 응답
        return ChatResponse(response=generate_fallback_response(request.message, request.context))

    response_text = call_openai(system_prompt, user_message)
    return ChatResponse(response=response_text)


def generate_fallback_response(message: str, context: Optional[str]) -> str:
    """OpenAI API 없을 때 폴백 응답"""
    message_lower = message.lower()

    if "전체 수정" in message or "모든 에러" in message or "모두 수정" in message:
        # context에서 오류 정보 파싱 시도
        if context:
            edits = parse_errors_from_context(context)
            if edits:
                response = "다음과 같이 수정하겠습니다:\n\n"
                for edit in edits:
                    response += f"[수정:{edit['row']}:{edit['field']}:{edit['suggested']}]\n"
                response += "\n위 수정사항을 적용했습니다."
                return response
        return "오류 정보를 찾을 수 없습니다. 구체적인 수정 내용을 알려주세요."

    if "규칙" in message or "형식" in message:
        return """## 입력 규칙

**날짜 형식:** YYYY-MM-DD (예: 2024-05-20)
**금액:** 숫자만 입력 (예: 2060000)
**사원번호:** 중복 불가
**필수 필드:** 사원번호, 성명, 입사일, 급여, 생년월일

수정이 필요하시면 "N번 항목 수정해줘"라고 말씀해주세요."""

    if "왜" in message or "오류" in message:
        return "해당 값이 형식에 맞지 않거나 논리적으로 문제가 있습니다. 구체적인 셀을 알려주시면 자세히 설명드리겠습니다."

    return "죄송합니다. 요청을 이해하지 못했습니다. '전체 수정', '규칙 설명' 등으로 말씀해주세요."


def parse_errors_from_context(context: str) -> list:
    """컨텍스트에서 오류 정보 추출"""
    edits = []
    # 패턴: 행 N: 필드명 - 오류메시지 (현재값: X, 제안: Y)
    pattern = r"행\s*(\d+)[:\s]+([^\s-]+)\s*[-–]\s*[^(]+\(현재값?:\s*([^,)]+),?\s*제안:?\s*([^)]+)\)"
    matches = re.findall(pattern, context, re.IGNORECASE)

    for match in matches:
        row, field, current, suggested = match
        edits.append({
            "row": row.strip(),
            "field": field.strip(),
            "current": current.strip(),
            "suggested": suggested.strip()
        })

    # 간단한 패턴도 시도
    if not edits:
        simple_pattern = r"행\s*(\d+).*?([가-힣]+일|급여|성명|사원번호).*?→\s*([^\s,]+)"
        matches = re.findall(simple_pattern, context)
        for match in matches:
            row, field, suggested = match
            edits.append({
                "row": row.strip(),
                "field": field.strip(),
                "suggested": suggested.strip()
            })

    return edits
