"""
OpenAI API Client

AIProcessor: 프롬프트 기반 정규화/검증 및 챗 응답.
OpenAI 키가 없거나 라이브러리가 없으면 안전하게 폴백합니다.
"""

import json
from typing import Dict, Optional

import pandas as pd

try:
    # openai==1.x SDK
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # 안전 폴백

from .prompts import get_normalize_validate_prompt


class AIProcessor:
    """
    AI 기반 정규화 및 검증 처리
    
    - normalize_and_validate(): 표 정규화 + 오류 검출 요청
    - chat(): 현재 데이터 맥락 기반 대화
    """

    def __init__(self, api_key: str):
        """
        OpenAI 클라이언트 초기화

        Args:
            api_key: OpenAI API 키
        """
        self.api_key = api_key or ""
        self.client = None
        if OpenAI and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    def _has_client(self) -> bool:
        return self.client is not None

    def normalize_and_validate(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> dict:
        """
        DataFrame을 AI에게 전달해서 정규화 + 검증

        Args:
            df: 업로드된 원본 DataFrame
            column_mapping: {"컬럼1": "설명", "컬럼2": "설명", ...}

        Returns:
            {
                "normalized_data": [
                    {"row": 1, "columns": {"전화": "01012345678", ...}},
                ],
                "errors": [
                    {"row": 2, "column": "급여", "original_value": "5억", "error": "...", "suggestion": "..."}
                ]
            }
        """
        # 키/클라이언트가 없으면 안전 폴백
        if not self._has_client():
            return {
                "normalized_data": [],
                "errors": [],
                "summary": "OPENAI_API_KEY 미설정 또는 클라이언트 비활성화"
            }

        prompt = get_normalize_validate_prompt(df, column_mapping)

        try:
            # 최신 SDK의 Chat Completions 사용 (안정적)
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 한국 HR 데이터 정규화/검증 전문가입니다. 반드시 JSON만 반환하세요."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            content: Optional[str] = None
            if completion and completion.choices:
                content = completion.choices[0].message.content

            if not content:
                return {"normalized_data": [], "errors": [], "summary": "빈 응답"}

            # JSON 파싱 시도
            parsed = self._parse_json_content(content)
            if not parsed:
                return {"normalized_data": [], "errors": [], "summary": "JSON 파싱 실패"}

            # 키 정규화: normalized_rows → normalized_data 지원
            normalized_data = parsed.get("normalized_data") or parsed.get("normalized_rows") or []
            errors = parsed.get("errors") or []
            return {"normalized_data": normalized_data, "errors": errors}

        except Exception as e:
            return {"normalized_data": [], "errors": [], "summary": f"오류: {e}"}

    def chat(self, df: pd.DataFrame, message: str, column_mapping: Dict[str, str]) -> dict:
        """
        현재 데이터 샘플과 컬럼 설명을 맥락으로 한 챗 응답.
        클라이언트가 없으면 폴백 메시지 반환.
        """
        if not self._has_client():
            return {"response": "AI가 비활성화되어 있습니다.", "function_call": None}

        # 간단한 컨텍스트 구성
        context_table = df.head(10).to_markdown()
        column_desc = "\n".join([f"- {k}: {v}" for k, v in column_mapping.items()])
        user_prompt = (
            "다음은 현재 HR 데이터 샘플과 컬럼 설명입니다. 질문에 간결히 답하세요.\n\n"
            f"[데이터]\n{context_table}\n\n[컬럼 설명]\n{column_desc}\n\n[질문]\n{message}"
        )

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "한국어로 친절하고 정확하게 답변하세요."},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content if completion and completion.choices else ""
            return {"response": content or "", "function_call": None}
        except Exception as e:
            return {"response": f"오류: {e}", "function_call": None}

    @staticmethod
    def _parse_json_content(content: str) -> Optional[dict]:
        """
        모델 응답에서 JSON 추출. 코드블록 또는 텍스트 JSON 모두 처리.
        """
        # 코드블록 추출 시도
        if "```" in content:
            try:
                start = content.find("```")
                end = content.rfind("```")
                block = content[start + 3:end].strip()
                # 언어 힌트 제거 (예: ```json)
                if "\n" in block:
                    first_line, rest = block.split("\n", 1)
                    if first_line.strip().lower() in ("json", "python", "txt"):
                        block = rest
                return json.loads(block)
            except Exception:
                pass
        # 일반 JSON 파싱
        try:
            return json.loads(content)
        except Exception:
            return None
