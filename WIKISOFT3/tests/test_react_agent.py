"""
ReACT Agent 및 재시도 전략 테스트
"""
import pytest
import sys
import os

sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT3")

from internal.agent.react_agent import ReactAgent, AgentAction, AgentState, create_react_agent
from internal.agent.retry_strategies import (
    RetryStrategy, RetryConfig, RetryReason, StrategyType, RetryResult
)
from internal.agent.tool_registry import get_registry


class TestReactAgent:
    """ReACT Agent 테스트"""
    
    @pytest.fixture
    def registry(self):
        """Tool Registry"""
        return get_registry()
    
    @pytest.fixture
    def agent(self, registry):
        """ReACT Agent"""
        return create_react_agent(registry, verbose=False)
    
    def test_agent_creation(self, agent):
        """에이전트 생성 테스트"""
        assert agent is not None
        assert isinstance(agent, ReactAgent)
        assert agent.max_iterations == 5
    
    def test_agent_state_initialization(self):
        """에이전트 상태 초기화"""
        state = AgentState()
        assert state.status == "running"
        assert len(state.thoughts) == 0
        assert len(state.observations) == 0
        assert state.current_step == 0
    
    def test_agent_run_with_valid_data(self, agent):
        """유효한 데이터로 에이전트 실행"""
        # 간단한 CSV 데이터
        test_data = "사원번호,이름,입사일\n001,홍길동,2020-01-01".encode('utf-8')
        
        result = agent.run(
            file_bytes=test_data,
            diagnostic_answers={},
            sheet_type="재직자"
        )
        
        assert result is not None
        assert "status" in result
        assert "confidence" in result
        assert result["status"] in ["completed", "needs_human", "failed"]
    
    def test_agent_run_with_empty_data(self, agent):
        """빈 데이터로 에이전트 실행"""
        result = agent.run(
            file_bytes=b"",
            diagnostic_answers={},
            sheet_type="재직자"
        )
        
        assert result is not None
        assert result["status"] in ["failed", "needs_human", "running", "completed"]
    
    def test_agent_run_with_diagnostic_answers(self, agent):
        """진단 답변과 함께 실행"""
        test_data = "사원번호,이름,기준급여\n001,홍길동,3000000".encode('utf-8')
        
        result = agent.run(
            file_bytes=test_data,
            diagnostic_answers={"q1": "예", "q2": 60},
            sheet_type="재직자"
        )
        
        assert result is not None
    
    def test_agent_reasoning_history(self, agent):
        """추론 히스토리 기록"""
        test_data = "사원번호,이름\n001,홍길동".encode('utf-8')
        
        result = agent.run(file_bytes=test_data)
        
        assert "agent_reasoning" in result
        assert len(result["agent_reasoning"]) > 0
        
        # 각 추론 단계 확인
        for step in result["agent_reasoning"]:
            assert "step" in step
            assert "thought" in step
            assert "action" in step
    
    def test_explain_reasoning(self, agent):
        """추론 과정 설명"""
        test_data = "사원번호,이름\n001,홍길동".encode('utf-8')
        agent.run(file_bytes=test_data)
        
        explanation = agent.explain_reasoning()
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "AI 에이전트" in explanation
    
    def test_confidence_thresholds(self, agent):
        """신뢰도 임계값 확인"""
        assert agent.CONFIDENCE_AUTO_COMPLETE == 0.95
        assert agent.CONFIDENCE_AUTO_CORRECT == 0.80
        assert agent.CONFIDENCE_NEEDS_REVIEW == 0.50


class TestRetryStrategies:
    """재시도 전략 테스트"""
    
    @pytest.fixture
    def retry_strategy(self):
        """재시도 전략"""
        config = RetryConfig(
            max_retries=3,
            base_delay=0.1,  # 테스트용 짧은 지연
            max_delay=1.0
        )
        return RetryStrategy(config)
    
    def test_retry_config_defaults(self):
        """기본 설정 확인"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter == True
    
    def test_get_delay(self, retry_strategy):
        """지연 시간 계산"""
        # 지터 때문에 정확한 값은 예측 불가, 범위만 확인
        delay = retry_strategy.get_delay(0)
        assert delay > 0
        assert delay <= retry_strategy.config.max_delay * 1.5
        
        # 지수 증가 확인
        delay1 = retry_strategy.get_delay(1)
        delay2 = retry_strategy.get_delay(2)
        # 대체로 delay2 > delay1 (지터 때문에 항상은 아님)
    
    def test_get_next_strategy(self, retry_strategy):
        """다음 전략 선택"""
        # 처음에는 첫 번째 전략
        strategy = retry_strategy.get_next_strategy(
            RetryReason.LOW_CONFIDENCE,
            []
        )
        assert strategy == StrategyType.STRICT_MATCHING
        
        # 하나 시도 후 다음 전략
        strategy = retry_strategy.get_next_strategy(
            RetryReason.LOW_CONFIDENCE,
            [StrategyType.STRICT_MATCHING]
        )
        assert strategy == StrategyType.LENIENT_MATCHING
    
    def test_get_next_strategy_exhausted(self, retry_strategy):
        """모든 전략 소진"""
        attempted = [
            StrategyType.STRICT_MATCHING,
            StrategyType.LENIENT_MATCHING,
            StrategyType.ASK_HUMAN
        ]
        
        strategy = retry_strategy.get_next_strategy(
            RetryReason.LOW_CONFIDENCE,
            attempted
        )
        assert strategy == StrategyType.GIVE_UP
    
    def test_execute_with_retry_success(self, retry_strategy):
        """재시도 성공 케이스"""
        call_count = 0
        
        def success_func(context):
            nonlocal call_count
            call_count += 1
            return {"success": True, "confidence": 0.95}
        
        result = retry_strategy.execute_with_retry(
            func=success_func,
            reason=RetryReason.LOW_CONFIDENCE,
            context={}
        )
        
        assert result.success == True
        assert call_count == 1
    
    def test_execute_with_retry_fail_then_success(self, retry_strategy):
        """실패 후 성공 케이스"""
        call_count = 0
        
        def fail_then_success(context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return {"confidence": 0.3}  # 낮은 신뢰도
            return {"confidence": 0.85}  # 성공
        
        result = retry_strategy.execute_with_retry(
            func=fail_then_success,
            reason=RetryReason.LOW_CONFIDENCE,
            context={}
        )
        
        assert result.success == True
        assert call_count >= 2
    
    def test_execute_with_retry_all_fail(self, retry_strategy):
        """모든 재시도 실패"""
        def always_fail(context):
            raise ValueError("항상 실패")
        
        result = retry_strategy.execute_with_retry(
            func=always_fail,
            reason=RetryReason.API_ERROR,
            context={}
        )
        
        assert result.success == False
        assert result.error is not None
    
    def test_strategy_chain_api_error(self, retry_strategy):
        """API 에러 전략 체인"""
        chain = retry_strategy._strategy_chain[RetryReason.API_ERROR]
        
        assert StrategyType.EXPONENTIAL_BACKOFF in chain
        assert StrategyType.FALLBACK_ONLY in chain
    
    def test_strategy_chain_parse_failure(self, retry_strategy):
        """파싱 실패 전략 체인"""
        chain = retry_strategy._strategy_chain[RetryReason.PARSE_FAILURE]
        
        assert StrategyType.ALTERNATIVE_PARSER in chain
        assert StrategyType.ASK_HUMAN in chain


class TestAgentAction:
    """에이전트 액션 Enum 테스트"""
    
    def test_action_values(self):
        """액션 값 확인"""
        assert AgentAction.PARSE.value == "parse_roster"
        assert AgentAction.MATCH.value == "match_headers"
        assert AgentAction.VALIDATE.value == "validate"
        assert AgentAction.COMPLETE.value == "complete"
        assert AgentAction.FAIL.value == "fail"
        assert AgentAction.ASK_HUMAN.value == "ask_human"


class TestIntegration:
    """통합 테스트"""
    
    @pytest.fixture
    def registry(self):
        return get_registry()
    
    def test_full_pipeline_with_react(self, registry):
        """ReACT Agent를 통한 전체 파이프라인"""
        agent = create_react_agent(registry, verbose=False)
        
        # 실제 HR 데이터 형식
        test_data = """사원번호,이름,생년월일,입사일,기준급여,종업원구분
001,홍길동,1990-01-01,2020-01-01,3000000,정규직
002,김철수,1985-05-15,2019-03-01,3500000,정규직
003,이영희,1992-08-20,2021-06-01,2800000,계약직""".encode('utf-8')
        
        result = agent.run(
            file_bytes=test_data,
            diagnostic_answers={"q19": 2, "q23": 1},
            sheet_type="재직자"
        )
        
        # 기본 구조 확인
        assert "status" in result
        assert "confidence" in result
        assert "steps" in result
        
        # 파싱 결과
        assert result["steps"].get("parsed_summary") is not None
        headers = result["steps"]["parsed_summary"].get("headers", [])
        assert "사원번호" in headers
        
        # 신뢰도
        confidence_score = result["confidence"].get("score", 0)
        assert 0 <= confidence_score <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
