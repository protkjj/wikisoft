import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI, OpenAI


class LLMClient:
    """LLM 클라이언트: Azure OpenAI 우선, 없으면 OpenAI 기본."""

    def __init__(self):
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        azure_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

        openai_key = os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if azure_endpoint and azure_key and azure_deployment:
            self.provider = "azure-openai"
            self.model = azure_deployment
            self.client = AzureOpenAI(
                api_key=azure_key,
                api_version=azure_version,
                azure_endpoint=azure_endpoint,
            )
        elif openai_key:
            self.provider = "openai"
            self.model = openai_model
            self.client = OpenAI(api_key=openai_key)
        else:
            raise ValueError("No OpenAI/Azure OpenAI credentials found in environment variables")

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.2, max_tokens: int = 600) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_with_tools(
        self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.2
    ) -> Dict[str, Any]:
        """툴 호출 지원하는 채팅 (OpenAI function calling)"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 800,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        result = {"content": message.content or ""}
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ]
        return result


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    return LLMClient()
