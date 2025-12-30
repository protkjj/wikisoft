"""
Tool Registry: 모든 Agent Tool 중앙 관리

각 Tool은:
- name: 고유 ID
- description: LLM이 이해할 설명
- input_schema: 입력 파라미터
- execute: 실제 실행 로직
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    """Tool 분류"""
    PARSER = "parser"      # Excel 파싱
    VALIDATOR = "validator"  # 검증
    ANALYZER = "analyzer"    # 분석
    CORRECTOR = "corrector"  # 수정
    HELPER = "helper"        # 보조


@dataclass
class ToolParameter:
    """Tool 입력 파라미터 정의"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass
class Tool:
    """Tool 정의"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    execute: Callable
    cost: Dict[str, float] = None  # {"time": 2.0, "tokens": 500}
    
    def __post_init__(self):
        if self.cost is None:
            self.cost = {"time": 1.0, "tokens": 100}
    
    def describe(self) -> Dict[str, Any]:
        """LLM이 이해할 형식으로 tool 설명"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                }
                for p in self.parameters
            ],
            "estimated_cost": self.cost,
        }


class ToolRegistry:
    """
    Tool 중앙 관리소
    
    ReACT Loop에서 사용:
    1. registry.list() - 사용 가능한 tool 목록
    2. registry.get(name) - tool 조회
    3. registry.call(name, **kwargs) - tool 실행
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._call_history: List[Dict[str, Any]] = []
    
    def register(self, tool: Tool) -> None:
        """Tool 등록"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
        print(f"✅ Tool registered: {tool.name}")
    
    def get(self, name: str) -> Optional[Tool]:
        """Tool 조회"""
        return self._tools.get(name)
    
    def list(self, category: Optional[ToolCategory] = None) -> List[Tool]:
        """Tool 목록 (선택적으로 category로 필터링)"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def describe_all(self) -> Dict[str, Any]:
        """모든 Tool을 LLM이 이해할 형식으로 설명"""
        return {
            "total_tools": len(self._tools),
            "tools": [tool.describe() for tool in self._tools.values()],
        }
    
    async def call(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Tool 실행
        
        Args:
            name: tool name
            **kwargs: tool 입력 파라미터
        
        Returns:
            {
                "success": bool,
                "result": Any,
                "error": Optional[str],
                "execution_time": float,
                "tokens_used": int,
            }
        """
        import time
        import asyncio
        
        tool = self.get(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "execution_time": 0,
                "tokens_used": 0,
            }
        
        try:
            start_time = time.time()
            
            # Tool 실행 (비동기/동기 모두 지원)
            if asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**kwargs)
            else:
                result = tool.execute(**kwargs)
            
            execution_time = time.time() - start_time
            
            call_record = {
                "tool": name,
                "params": kwargs,
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": time.time(),
            }
            self._call_history.append(call_record)
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tokens_used": int(tool.cost.get("tokens", 100) * (execution_time / tool.cost.get("time", 1))),
            }
        
        except Exception as e:
            call_record = {
                "tool": name,
                "params": kwargs,
                "success": False,
                "error": str(e),
                "timestamp": time.time(),
            }
            self._call_history.append(call_record)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0,
                "tokens_used": 0,
            }
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Tool 실행 이력 조회"""
        return self._call_history
    
    def clear_history(self) -> None:
        """Tool 실행 이력 초기화"""
        self._call_history.clear()


# 전역 registry 인스턴스
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """전역 registry 조회"""
    return _global_registry
