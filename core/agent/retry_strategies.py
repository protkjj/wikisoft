"""
재시도 전략 모듈

다양한 실패 상황에 대한 재시도 전략:
- 지수 백오프
- 대안 전략 (다른 파싱 방법, 다른 매칭 전략)
- 사람에게 질문
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import time
import random


class RetryReason(Enum):
    """재시도 사유"""
    LOW_CONFIDENCE = "low_confidence"
    PARSE_FAILURE = "parse_failure"
    MATCH_FAILURE = "match_failure"
    VALIDATE_FAILURE = "validate_failure"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"


class StrategyType(Enum):
    """전략 유형"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    STRICT_MATCHING = "strict_matching"
    LENIENT_MATCHING = "lenient_matching"
    ALTERNATIVE_PARSER = "alternative_parser"
    FALLBACK_ONLY = "fallback_only"
    ASK_HUMAN = "ask_human"
    GIVE_UP = "give_up"


@dataclass
class RetryConfig:
    """재시도 설정"""
    max_retries: int = 3
    base_delay: float = 1.0  # 초
    max_delay: float = 30.0  # 최대 대기 시간
    exponential_base: float = 2.0
    jitter: bool = True  # 랜덤 지터 추가


@dataclass
class RetryResult:
    """재시도 결과"""
    success: bool
    strategy_used: StrategyType
    attempts: int
    final_result: Any
    error: Optional[str] = None
    delay_total: float = 0.0


class RetryStrategy:
    """재시도 전략 관리자"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._strategy_chain: Dict[RetryReason, List[StrategyType]] = {
            RetryReason.LOW_CONFIDENCE: [
                StrategyType.STRICT_MATCHING,
                StrategyType.LENIENT_MATCHING,
                StrategyType.ASK_HUMAN,
            ],
            RetryReason.PARSE_FAILURE: [
                StrategyType.ALTERNATIVE_PARSER,
                StrategyType.ASK_HUMAN,
            ],
            RetryReason.MATCH_FAILURE: [
                StrategyType.FALLBACK_ONLY,
                StrategyType.LENIENT_MATCHING,
                StrategyType.ASK_HUMAN,
            ],
            RetryReason.API_ERROR: [
                StrategyType.EXPONENTIAL_BACKOFF,
                StrategyType.FALLBACK_ONLY,
            ],
            RetryReason.TIMEOUT: [
                StrategyType.EXPONENTIAL_BACKOFF,
                StrategyType.FALLBACK_ONLY,
            ],
            RetryReason.RATE_LIMIT: [
                StrategyType.EXPONENTIAL_BACKOFF,
            ],
        }
    
    def get_delay(self, attempt: int) -> float:
        """지수 백오프 지연 시간 계산"""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # 0.5 ~ 1.5 배 사이의 랜덤 지터
            delay *= (0.5 + random.random())
        
        return delay
    
    def get_next_strategy(
        self,
        reason: RetryReason,
        attempted_strategies: List[StrategyType]
    ) -> Optional[StrategyType]:
        """다음 시도할 전략 반환"""
        chain = self._strategy_chain.get(reason, [])
        
        for strategy in chain:
            if strategy not in attempted_strategies:
                return strategy
        
        return StrategyType.GIVE_UP
    
    def execute_with_retry(
        self,
        func: Callable,
        reason: RetryReason,
        context: Dict[str, Any],
        on_strategy_change: Optional[Callable[[StrategyType], None]] = None
    ) -> RetryResult:
        """
        재시도 로직으로 함수 실행
        
        Args:
            func: 실행할 함수 (context를 받아서 결과 반환)
            reason: 재시도 사유
            context: 컨텍스트 데이터
            on_strategy_change: 전략 변경 시 콜백
        
        Returns:
            RetryResult
        """
        attempted_strategies: List[StrategyType] = []
        total_delay = 0.0
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            # 현재 전략 결정
            if attempt == 0:
                current_strategy = None
            else:
                current_strategy = self.get_next_strategy(reason, attempted_strategies)
                
                if current_strategy == StrategyType.GIVE_UP:
                    break
                
                if current_strategy:
                    attempted_strategies.append(current_strategy)
                    
                    if on_strategy_change:
                        on_strategy_change(current_strategy)
                    
                    # 전략에 따라 컨텍스트 수정
                    context = self._apply_strategy(current_strategy, context)
                
                # 지연
                if current_strategy == StrategyType.EXPONENTIAL_BACKOFF:
                    delay = self.get_delay(attempt)
                    time.sleep(delay)
                    total_delay += delay
            
            try:
                result = func(context)
                
                # 성공 조건 확인
                if self._is_success(result, reason):
                    return RetryResult(
                        success=True,
                        strategy_used=current_strategy or StrategyType.EXPONENTIAL_BACKOFF,
                        attempts=attempt + 1,
                        final_result=result,
                        delay_total=total_delay
                    )
                
                # 신뢰도가 낮으면 다음 전략 시도
                last_error = f"Result confidence too low: {result.get('confidence', 0)}"
                
            except Exception as e:
                last_error = str(e)
                print(f"[Retry] Attempt {attempt + 1} failed: {e}")
        
        # 모든 재시도 실패
        return RetryResult(
            success=False,
            strategy_used=StrategyType.GIVE_UP,
            attempts=self.config.max_retries + 1,
            final_result=None,
            error=last_error,
            delay_total=total_delay
        )
    
    def _apply_strategy(self, strategy: StrategyType, context: Dict[str, Any]) -> Dict[str, Any]:
        """전략에 따라 컨텍스트 수정"""
        new_context = context.copy()
        
        if strategy == StrategyType.STRICT_MATCHING:
            new_context["confidence_threshold"] = 0.90
            new_context["use_ai"] = True
            
        elif strategy == StrategyType.LENIENT_MATCHING:
            new_context["confidence_threshold"] = 0.50
            new_context["use_ai"] = True
            
        elif strategy == StrategyType.FALLBACK_ONLY:
            new_context["use_ai"] = False
            new_context["fallback_only"] = True
            
        elif strategy == StrategyType.ALTERNATIVE_PARSER:
            # 다른 인코딩 시도
            current_encoding = context.get("encoding", "utf-8")
            encodings = ["utf-8", "cp949", "euc-kr", "latin1"]
            try:
                idx = encodings.index(current_encoding)
                new_context["encoding"] = encodings[(idx + 1) % len(encodings)]
            except ValueError:
                new_context["encoding"] = "cp949"
        
        return new_context
    
    def _is_success(self, result: Any, reason: RetryReason) -> bool:
        """성공 여부 판단"""
        if result is None:
            return False
        
        if isinstance(result, dict):
            # 에러 체크
            if result.get("error"):
                return False
            
            # 신뢰도 체크
            confidence = result.get("confidence", 0)
            if isinstance(confidence, dict):
                confidence = confidence.get("score", 0)
            
            if reason == RetryReason.LOW_CONFIDENCE:
                return confidence >= 0.70  # 재시도 시에는 조금 낮은 임계값
            
            return True
        
        return bool(result)


class AsyncRetryStrategy(RetryStrategy):
    """비동기 재시도 전략"""
    
    async def execute_with_retry_async(
        self,
        func: Callable,
        reason: RetryReason,
        context: Dict[str, Any],
        on_strategy_change: Optional[Callable[[StrategyType], None]] = None
    ) -> RetryResult:
        """비동기 재시도 실행"""
        import asyncio
        
        attempted_strategies: List[StrategyType] = []
        total_delay = 0.0
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            if attempt > 0:
                current_strategy = self.get_next_strategy(reason, attempted_strategies)
                
                if current_strategy == StrategyType.GIVE_UP:
                    break
                
                if current_strategy:
                    attempted_strategies.append(current_strategy)
                    
                    if on_strategy_change:
                        on_strategy_change(current_strategy)
                    
                    context = self._apply_strategy(current_strategy, context)
                
                if current_strategy == StrategyType.EXPONENTIAL_BACKOFF:
                    delay = self.get_delay(attempt)
                    await asyncio.sleep(delay)
                    total_delay += delay
            else:
                current_strategy = None
            
            try:
                # 비동기 함수 지원
                if asyncio.iscoroutinefunction(func):
                    result = await func(context)
                else:
                    result = func(context)
                
                if self._is_success(result, reason):
                    return RetryResult(
                        success=True,
                        strategy_used=current_strategy or StrategyType.EXPONENTIAL_BACKOFF,
                        attempts=attempt + 1,
                        final_result=result,
                        delay_total=total_delay
                    )
                
                last_error = f"Result not satisfactory"
                
            except Exception as e:
                last_error = str(e)
                print(f"[AsyncRetry] Attempt {attempt + 1} failed: {e}")
        
        return RetryResult(
            success=False,
            strategy_used=StrategyType.GIVE_UP,
            attempts=self.config.max_retries + 1,
            final_result=None,
            error=last_error,
            delay_total=total_delay
        )


# 전역 인스턴스
_retry_strategy: Optional[RetryStrategy] = None


def get_retry_strategy() -> RetryStrategy:
    """전역 재시도 전략 인스턴스"""
    global _retry_strategy
    if _retry_strategy is None:
        _retry_strategy = RetryStrategy()
    return _retry_strategy


def get_async_retry_strategy() -> AsyncRetryStrategy:
    """비동기 재시도 전략 인스턴스"""
    return AsyncRetryStrategy()
