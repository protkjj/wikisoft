"""
Tool Registry: 파서/매칭/검증/리포트 도구를 중앙에서 관리
"""
from typing import Any, Callable, Dict, List

from internal.ai.matcher import match_headers
from internal.ai.knowledge_base import add_error_rule, learn_from_correction
from internal.generators.report import generate_report
from internal.parsers.parser import parse_roster
from internal.validators.validator import validate
from internal.validators.duplicate_detector import detect_duplicates


class ToolRegistry:
    """Tool 레지스트리: Agent가 호출 가능한 도구들을 관리."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {
            "parse_roster": {
                "func": parse_roster,
                "description": "Excel/CSV 파일 파싱",
                "params": ["file_bytes", "sheet_name", "max_rows"],
            },
            "match_headers": {
                "func": match_headers,
                "description": "고객 헤더를 표준 스키마에 매칭",
                "params": ["parsed", "sheet_type"],
            },
            "validate": {
                "func": validate,
                "description": "파싱/매칭 결과 유효성 검사 (L1/L2)",
                "params": ["parsed", "matches"],
            },
            "generate_report": {
                "func": generate_report,
                "description": "검증 결과 리포트 생성",
                "params": ["validation"],
            },
            "detect_duplicates": {
                "func": detect_duplicates,
                "description": "중복 행 탐지 (완전/유사/의심)",
                "params": ["df", "headers", "matches"],
            },
            "add_error_rule": {
                "func": add_error_rule,
                "description": "새로운 오류 검증 규칙 학습",
                "params": ["field", "condition", "message", "severity", "category"],
            },
            "learn_from_correction": {
                "func": learn_from_correction,
                "description": "사용자 수정에서 패턴 학습",
                "params": ["field", "original_value", "was_error", "correct_interpretation", "diagnostic_context"],
            },
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [{"name": name, "description": info["description"], "params": info["params"]} for name, info in self.tools.items()]

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        func = self.tools[tool_name]["func"]
        return func(**kwargs)

    def get_tool(self, tool_name: str) -> Callable:
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        return self.tools[tool_name]["func"]


# 글로벌 레지스트리
_registry = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
