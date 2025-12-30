"""
ReACT Loop: Reasoning + Acting

Agent의 핵심 루프:
1. THINK: LLM이 상황 분석
2. ACT: Tool 선택 및 실행
3. OBSERVE: 결과 관찰
4. REPEAT: 목표 달성 시까지 반복
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import asyncio


class ActionType(str, Enum):
    """Action 타입"""
    PARSE = "parse"
    VALIDATE = "validate"
    ANALYZE = "analyze"
    CORRECT = "correct"
    DECIDE = "decide"
    REPORT = "report"


@dataclass
class Action:
    """LLM이 결정한 행동"""
    type: ActionType
    tool_name: str
    parameters: Dict[str, Any]
    reasoning: str
    confidence: float


@dataclass
class Observation:
    """도구 실행 결과"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class AgentState:
    """Agent의 상태"""
    file_path: str
    step: int = 0
    total_steps: int = 0
    thoughts: List[str] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    final_result: Optional[Dict[str, Any]] = None
    start_time: float = field(default_factory=time.time)


class ReACTLoop:
    """
    ReACT Loop 구현
    
    Reasoning + Acting의 반복으로 자동화된 의사결정을 수행합니다.
    """
    
    def __init__(self, registry, llm_client=None):
        """
        Args:
            registry: ToolRegistry 인스턴스
            llm_client: OpenAI LLM 클라이언트 (mock: None)
        """
        self.registry = registry
        self.llm_client = llm_client
    
    async def run(
        self,
        file_path: str,
        task: str = "validate",
        max_steps: int = 10,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        ReACT Loop 실행
        
        Args:
            file_path: 처리할 파일 경로
            task: 수행할 작업 (validate, analyze, correct 등)
            max_steps: 최대 반복 횟수
            confidence_threshold: 신뢰도 임계값
        
        Returns:
            {
                "success": bool,
                "task": str,
                "steps": int,
                "state": AgentState dict,
                "result": Dict[str, Any],
                "execution_time": float,
            }
        """
        state = AgentState(file_path=file_path, total_steps=max_steps)
        start_time = time.time()
        
        try:
            # Step 0: 초기화 (Mock LLM)
            initial_thought = await self._think(state, task)
            state.thoughts.append(initial_thought)
            
            # Loop: ReACT 반복
            while state.step < max_steps:
                state.step += 1
                
                # 1. THINK: 다음 action 결정
                thought = await self._think(state, task)
                state.thoughts.append(thought)
                
                # 2. ACT: Action 실행
                action = await self._decide_action(state, task)
                if not action:
                    break  # 더 이상 할 action이 없음
                
                state.actions.append(action)
                
                # 3. OBSERVE: Tool 실행 및 결과 관찰
                observation = await self._execute_action(action)
                state.observations.append(observation)
                
                # 4. 의사결정 기록
                decision = {
                    "step": state.step,
                    "action": action.tool_name,
                    "success": observation.success,
                    "confidence": action.confidence,
                }
                state.decisions.append(decision)
                
                # 5. 종료 조건 확인
                if self._should_stop(state, observation, confidence_threshold):
                    break
            
            # 최종 결과 생성
            state.final_result = {
                "status": "completed",
                "task": task,
                "steps_taken": state.step,
                "total_actions": len(state.actions),
                "successful_actions": sum(1 for o in state.observations if o.success),
                "confidence": self._calculate_overall_confidence(state),
                "summary": self._summarize_state(state),
            }
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "task": task,
                "steps": state.step,
                "state": self._state_to_dict(state),
                "result": state.final_result,
                "execution_time": round(execution_time, 3),
                "total_tokens": sum(o.tokens_used for o in state.observations),
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "steps": state.step,
                "execution_time": round(execution_time, 3),
            }
    
    async def _think(self, state: AgentState, task: str) -> str:
        """
        THINK: 현재 상황 분석 (Mock LLM)
        
        실제 환경에서는 OpenAI API 호출
        """
        context = {
            "file": state.file_path,
            "task": task,
            "step": state.step,
            "actions_taken": len(state.actions),
            "recent_observations": [
                o.success for o in state.observations[-3:]
            ] if state.observations else [],
        }
        
        # Mock LLM response
        if state.step == 0:
            thought = f"분석: {task} 작업 시작. 파일: {state.file_path}"
        elif state.step < 3:
            thought = f"Step {state.step}: 초기 검증 중..."
        else:
            thought = f"Step {state.step}: 의사결정 단계. 신뢰도 평가 필요"
        
        return thought
    
    async def _decide_action(self, state: AgentState, task: str) -> Optional[Action]:
        """
        다음 실행할 Action 결정
        
        Mock: 순차적으로 Tool을 실행
        """
        available_tools = self.registry.list()
        
        if not available_tools:
            return None
        
        # Step별로 다른 tool 선택 (Mock)
        step = state.step % len(available_tools)
        tool = available_tools[step]
        
        action = Action(
            type=ActionType(task),
            tool_name=tool.name,
            parameters={"file_path": state.file_path},
            reasoning=f"Step {state.step}: {tool.description}를 실행합니다",
            confidence=0.7 + (state.step * 0.05),  # 신뢰도 증가
        )
        
        return action
    
    async def _execute_action(self, action: Action) -> Observation:
        """
        Action 실행 및 결과 반환
        """
        try:
            result = await self.registry.call(
                action.tool_name,
                **action.parameters
            )
            
            return Observation(
                success=result.get("success", True),
                result=result.get("result"),
                error=result.get("error"),
                execution_time=result.get("execution_time", 0),
                tokens_used=result.get("tokens_used", 0),
            )
        except Exception as e:
            return Observation(
                success=False,
                result=None,
                error=str(e),
                execution_time=0,
                tokens_used=0,
            )
    
    def _should_stop(
        self,
        state: AgentState,
        observation: Observation,
        confidence_threshold: float
    ) -> bool:
        """
        종료 조건 확인
        """
        # 신뢰도 높으면 종료
        if self._calculate_overall_confidence(state) >= confidence_threshold:
            return True
        
        # 실패가 많으면 종료
        success_rate = sum(1 for o in state.observations if o.success) / max(len(state.observations), 1)
        if success_rate < 0.3 and len(state.observations) > 3:
            return True
        
        # Step 초과 시 종료 (loop에서 확인)
        return False
    
    def _calculate_overall_confidence(self, state: AgentState) -> float:
        """전체 신뢰도 계산"""
        if not state.actions:
            return 0.0
        
        action_confidences = [a.confidence for a in state.actions]
        observation_successes = [1.0 if o.success else 0.0 for o in state.observations]
        
        action_score = sum(action_confidences) / len(action_confidences) if action_confidences else 0.0
        observation_score = sum(observation_successes) / len(observation_successes) if observation_successes else 0.0
        
        overall = (action_score * 0.4 + observation_score * 0.6)
        return round(overall, 3)
    
    def _summarize_state(self, state: AgentState) -> str:
        """State 요약"""
        return (
            f"총 {state.step}단계 실행. "
            f"성공: {sum(1 for o in state.observations if o.success)}/{len(state.observations)}. "
            f"신뢰도: {self._calculate_overall_confidence(state):.1%}"
        )
    
    def _state_to_dict(self, state: AgentState) -> Dict[str, Any]:
        """AgentState를 딕셔너리로 변환"""
        return {
            "file_path": state.file_path,
            "step": state.step,
            "total_steps": state.total_steps,
            "thoughts": state.thoughts,
            "actions": [
                {
                    "type": a.type.value,
                    "tool": a.tool_name,
                    "confidence": a.confidence,
                    "reasoning": a.reasoning,
                }
                for a in state.actions
            ],
            "observations": [
                {
                    "success": o.success,
                    "error": o.error,
                    "execution_time": o.execution_time,
                }
                for o in state.observations
            ],
            "decisions": state.decisions,
        }
