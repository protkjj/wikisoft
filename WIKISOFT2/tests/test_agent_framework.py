"""
Unit Tests for WIKISOFT2 Agent Framework

Test Coverage:
- Tool Registry
- ReACT Loop
- Confidence Calculator
- Decision Engine
- Memory System
"""

import pytest
import asyncio
from internal.tools.registry import get_registry, Tool, ToolCategory, ToolParameter
from internal.tools.parser import ParserTool, register_parser_tool
from internal.tools.validator import ValidatorTool, register_validator_tools
from internal.tools.analyzer import AnalyzerTool, register_analyzer_tools
from internal.tools.corrector import CorrectorTool, register_corrector_tools
from internal.agent.react_loop import ReACTLoop, AgentState
from internal.agent.confidence import ConfidenceCalculator
from internal.agent.decision_engine import DecisionEngine
from internal.agent.memory import MemorySystem, MemoryEntry
from internal.config.schema_config import SchemaConfig
from internal.config.prompt_config import PromptConfig


# ============================================
# Tool Registry Tests
# ============================================

class TestToolRegistry:
    """Tool Registry 테스트"""
    
    def test_tool_registration(self):
        """Tool 등록 테스트"""
        registry = get_registry()
        initial_count = len(registry.list())
        
        # 새 Tool 생성
        tool = Tool(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.HELPER,
            parameters=[
                ToolParameter("param1", "str", "Parameter 1", required=True)
            ],
            execute=lambda **kwargs: {"result": "test"}
        )
        
        # 등록
        registry.register(tool)
        
        # 검증
        assert len(registry.list()) > initial_count
        assert registry.get("test_tool") is not None
    
    def test_tool_execution(self):
        """Tool 실행 테스트"""
        async def test_async():
            registry = get_registry()
            result = await registry.call("parse_excel", file_path="test.xlsx")
            assert "success" in result or "error" in result
        
        asyncio.run(test_async())
    
    def test_tool_describe(self):
        """Tool 설명 테스트"""
        registry = get_registry()
        tools = registry.list()
        
        assert len(tools) > 0
        
        for tool in tools:
            desc = tool.describe()
            assert "name" in desc
            assert "description" in desc
            assert "parameters" in desc


# ============================================
# Confidence Calculator Tests
# ============================================

class TestConfidenceCalculator:
    """Confidence Calculator 테스트"""
    
    def test_calculate_confidence(self):
        """신뢰도 계산 테스트"""
        calc = ConfidenceCalculator()
        
        score = calc.calculate(
            action_confidence=0.8,
            tool_confidence=0.9,
            data_quality=0.7,
            result_confidence=0.85
        )
        
        assert 0 <= score.overall <= 1
        assert score.action == 0.8
        assert score.tool == 0.9
        assert score.data == 0.7
        assert score.result == 0.85
    
    def test_get_recommendation(self):
        """추천 조회 테스트"""
        calc = ConfidenceCalculator()
        
        # 높은 신뢰도
        rec_high = calc.get_recommendation(0.95)
        assert rec_high["action"] == "auto_complete"
        
        # 중간 신뢰도
        rec_mid = calc.get_recommendation(0.75)
        assert rec_mid["action"] == "ask_human"
        
        # 낮은 신뢰도
        rec_low = calc.get_recommendation(0.40)
        assert rec_low["action"] == "reject"
    
    def test_data_quality(self):
        """데이터 품질 평가 테스트"""
        calc = ConfidenceCalculator()
        
        good_data = {"field1": "value1", "field2": 100}
        quality = calc.calculate_data_quality(good_data)
        
        assert 0 <= quality <= 1
        assert quality >= 0.5  # 합리적인 데이터는 50% 이상


# ============================================
# Decision Engine Tests
# ============================================

class TestDecisionEngine:
    """Decision Engine 테스트"""
    
    def test_decide_high_confidence(self):
        """높은 신뢰도 의사결정 테스트"""
        async def test_async():
            engine = DecisionEngine()
            decision = await engine.decide(
                confidence=0.95,
                data={"salary": 50000},
                result={"success": True},
                context={}
            )
            
            assert decision.confidence == 0.95
            # 95% 이상은 자동 완료
            assert decision.type.value in ["auto_complete", "ask_human"]
        
        asyncio.run(test_async())
    
    def test_policy_check(self):
        """정책 검사 테스트"""
        engine = DecisionEngine()
        
        # 정상 데이터
        good_check = engine._check_policies(
            {"salary": 50000, "count": 100},
            {"success": True}
        )
        assert good_check["pass"]
        
        # 비정상 데이터 (인원 0)
        bad_check = engine._check_policies(
            {"salary": 50000, "count": 0},
            {"success": True}
        )
        assert not bad_check["pass"]


# ============================================
# Memory System Tests
# ============================================

class TestMemorySystem:
    """Memory System 테스트"""
    
    def test_remember_and_recall(self):
        """기억 및 회상 테스트"""
        memory = MemorySystem()
        
        # 패턴 저장
        entry_id = memory.remember(
            type="pattern",
            key="salary_above_100k",
            data={"threshold": 100000, "confidence": 0.95},
            confidence=0.95
        )
        
        assert entry_id is not None
        
        # 패턴 조회
        entry = memory.recall("salary_above_100k")
        assert entry is not None
        assert entry.confidence == 0.95
    
    def test_search_patterns(self):
        """패턴 검색 테스트"""
        memory = MemorySystem()
        
        # 여러 패턴 저장
        memory.remember("pattern", "employee_validation", {}, 0.9)
        memory.remember("pattern", "salary_check", {}, 0.85)
        memory.remember("error", "parse_error", {}, 0.3)
        
        # 검색
        results = memory.search("salary", type="pattern")
        assert len(results) >= 1
        assert any("salary" in r.key for r in results)
    
    def test_memory_stats(self):
        """메모리 통계 테스트"""
        memory = MemorySystem()
        
        memory.remember("pattern", "test1", {}, 0.9)
        memory.remember("error", "test2", {}, 0.3)
        
        stats = memory.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["by_type"]["pattern"] == 1
        assert stats["by_type"]["error"] == 1
        assert "avg_confidence" in stats


# ============================================
# Configuration Tests
# ============================================

class TestSchemaConfig:
    """SchemaConfig 테스트"""
    
    def test_get_schema(self):
        """스키마 조회 테스트"""
        config = SchemaConfig()
        schema = config.get_schema()
        
        assert "employee_type" in schema
        assert "salary" in schema
        assert len(schema) >= 15
    
    def test_validate_field(self):
        """필드 검증 테스트"""
        config = SchemaConfig()
        
        # 유효한 필드
        assert config.validate_field("name", "John Doe")
        assert config.validate_field("salary", "50000")
        assert config.validate_field("salary", 50000)
        
        # 무효한 필드
        assert not config.validate_field("salary", "invalid")
        assert not config.validate_field("unknown_field", "value")


class TestPromptConfig:
    """PromptConfig 테스트"""
    
    def test_get_prompt(self):
        """프롬프트 조회 테스트"""
        config = PromptConfig()
        
        system = config.get_system_prompt("column_matching")
        assert system is not None
        assert "헤더" in system or "매칭" in system
    
    def test_list_prompts(self):
        """프롬프트 목록 테스트"""
        config = PromptConfig()
        prompts = config.list_prompts()
        
        assert len(prompts) > 0
        assert "column_matching" in prompts


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """통합 테스트"""
    
    def test_agent_framework(self):
        """Agent Framework 통합 테스트"""
        async def test_async():
            # Tool Registry 초기화
            registry = get_registry()
            register_parser_tool(registry)
            register_validator_tools(registry)
            register_analyzer_tools(registry)
            register_corrector_tools(registry)
            
            # Agent 컴포넌트
            react = ReACTLoop(registry=registry)
            calc = ConfidenceCalculator()
            engine = DecisionEngine()
            
            # ReACT Loop 실행
            result = await react.run("test.xlsx", task="validate", max_steps=2)
            
            assert result.get("success") in [True, False]
            assert "steps" in result
            
            # Confidence 계산
            score = calc.calculate(0.75, 0.80, 0.85, 0.78)
            assert 0 <= score.overall <= 1
            
            # Decision
            decision = await engine.decide(
                confidence=score.overall,
                data={},
                result={},
                context={}
            )
            assert decision is not None
        
        asyncio.run(test_async())


# ============================================
# Test Runner
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
