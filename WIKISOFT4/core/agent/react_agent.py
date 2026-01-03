"""
ReACT Agent: Think → Act → Observe 루프 기반 자율적 의사결정

ReACT (Reasoning and Acting) 패턴:
1. Think: 현재 상황 분석, 다음 액션 결정
2. Act: 도구 실행
3. Observe: 결과 관찰, 신뢰도 체크
4. 반복 or 종료

특징:
- 자율적 재시도 (신뢰도 < 임계값이면 다른 전략 시도)
- 사람 개입 요청 (해결 불가능하면 에스컬레이션)
- 추론 과정 투명하게 기록
- LLM 기반 추론 (선택적)
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentAction(Enum):
    """에이전트 액션 타입."""
    PARSE = "parse_roster"
    MATCH = "match_headers"
    VALIDATE = "validate"
    REPORT = "generate_report"
    ASK_HUMAN = "ask_human"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass
class Thought:
    """에이전트의 사고 과정."""
    step: int
    reasoning: str
    action: AgentAction
    action_params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class Observation:
    """액션 실행 결과."""
    action: AgentAction
    success: bool
    result: Any
    confidence: float = 0.0
    error: Optional[str] = None


@dataclass
class AgentState:
    """에이전트 상태."""
    thoughts: List[Thought] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    current_step: int = 0
    status: str = "running"  # running, completed, failed, needs_human
    final_result: Optional[Dict[str, Any]] = None
    
    def add_thought(self, thought: Thought):
        self.thoughts.append(thought)
        self.current_step = thought.step
    
    def add_observation(self, observation: Observation):
        self.observations.append(observation)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """추론 과정 히스토리."""
        history = []
        for t, o in zip(self.thoughts, self.observations):
            history.append({
                "step": t.step,
                "thought": t.reasoning,
                "action": t.action.value,
                "result_success": o.success,
                "confidence": o.confidence,
                "error": o.error,
            })
        return history


class ReactAgent:
    """
    ReACT 기반 자율 에이전트.
    
    특징:
    - Tool Registry에서 도구 선택
    - 신뢰도 기반 의사결정
    - 자동 재시도 (최대 N회)
    - 사람 개입 에스컬레이션
    """
    
    # 신뢰도 임계값
    CONFIDENCE_AUTO_COMPLETE = 0.95  # 이상이면 자동 완료
    CONFIDENCE_AUTO_CORRECT = 0.80   # 이상이면 자동 수정 + 알림
    CONFIDENCE_NEEDS_REVIEW = 0.50   # 미만이면 사람 검토 필요
    
    def __init__(
        self,
        tool_registry,
        llm_client: Optional[Callable] = None,
        max_iterations: int = 5,
        verbose: bool = True,
        use_llm_reasoning: bool = True  # LLM 추론 활성화 여부
    ):
        self.registry = tool_registry
        self.llm = llm_client
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.use_llm_reasoning = use_llm_reasoning and self._has_openai_key()
        self.state = AgentState()
        self.retry_count = 0  # 재시도 횟수 추적
    
    def _has_openai_key(self) -> bool:
        """OpenAI API 키 존재 여부 확인."""
        return bool(os.getenv("OPENAI_API_KEY"))
    
    def run(
        self,
        file_bytes: bytes,
        diagnostic_answers: Optional[Dict[str, Any]] = None,
        sheet_type: str = "재직자"
    ) -> Dict[str, Any]:
        """
        에이전트 실행: 파일 → 검증 결과.
        
        Args:
            file_bytes: 업로드된 파일
            diagnostic_answers: 진단 질문 답변
            sheet_type: 시트 타입
        
        Returns:
            최종 검증 결과 + 에이전트 추론 히스토리
        """
        self.state = AgentState()
        context = {
            "file_bytes": file_bytes,
            "diagnostic_answers": diagnostic_answers or {},
            "sheet_type": sheet_type,
            "parsed": None,
            "matches": None,
            "validation": None,
        }
        
        for i in range(self.max_iterations):
            # 1. Think: 다음 액션 결정
            thought = self._think(context, i + 1)
            self.state.add_thought(thought)
            
            if self.verbose:
                print(f"[Step {i+1}] Think: {thought.reasoning}")
                print(f"         Action: {thought.action.value}")
            
            # 2. 종료 조건 체크
            if thought.action == AgentAction.COMPLETE:
                self.state.status = "completed"
                break
            elif thought.action == AgentAction.FAIL:
                self.state.status = "failed"
                break
            elif thought.action == AgentAction.ASK_HUMAN:
                self.state.status = "needs_human"
                break
            
            # 3. Act: 도구 실행
            observation = self._act(thought, context)
            self.state.add_observation(observation)
            
            if self.verbose:
                print(f"         Result: {'✅' if observation.success else '❌'} (conf: {observation.confidence:.2f})")
            
            # 4. Observe: 결과 업데이트
            self._observe(observation, context, thought.action)
            
            # 5. 조기 종료 체크
            if observation.success and observation.confidence >= self.CONFIDENCE_AUTO_COMPLETE:
                if context.get("validation"):
                    self.state.status = "completed"
                    break
        
        # 최종 결과 구성
        return self._build_final_result(context)
    
    def _think(self, context: Dict[str, Any], step: int) -> Thought:
        """
        현재 상황 분석 및 다음 액션 결정.
        
        규칙 기반 + LLM 추론 (API 키 있을 때).
        """
        # 상태에 따른 규칙 기반 결정
        if context["parsed"] is None:
            return Thought(
                step=step,
                reasoning="파일이 파싱되지 않았습니다. 먼저 파싱을 수행합니다.",
                action=AgentAction.PARSE,
                action_params={"file_bytes": context["file_bytes"]},
            )
        
        if context["matches"] is None:
            return Thought(
                step=step,
                reasoning="헤더 매칭이 필요합니다. 표준 스키마에 매칭합니다.",
                action=AgentAction.MATCH,
                action_params={
                    "parsed": context["parsed"],
                    "sheet_type": context["sheet_type"],
                },
            )
        
        # 매칭 신뢰도 체크 + LLM 추론
        match_confidence = self._calculate_match_confidence(context["matches"])
        
        # 신뢰도가 낮고 재시도 가능하면 재시도
        if match_confidence < self.CONFIDENCE_AUTO_CORRECT and self.retry_count < 2:
            self.retry_count += 1
            reasoning = self._get_llm_reasoning(context, match_confidence) if self.use_llm_reasoning else \
                f"매칭 신뢰도가 낮습니다 ({match_confidence:.2f}). 재시도합니다. (시도 {self.retry_count}/2)"
            
            return Thought(
                step=step,
                reasoning=reasoning,
                action=AgentAction.MATCH,
                action_params={
                    "parsed": context["parsed"],
                    "sheet_type": context["sheet_type"],
                    "retry": True,  # 재시도 플래그
                },
                confidence=match_confidence,
            )
        
        if match_confidence < self.CONFIDENCE_NEEDS_REVIEW:
            reasoning = self._get_llm_reasoning(context, match_confidence) if self.use_llm_reasoning else \
                f"매칭 신뢰도가 낮습니다 ({match_confidence:.2f}). 사람의 검토가 필요합니다."
            
            return Thought(
                step=step,
                reasoning=reasoning,
                action=AgentAction.ASK_HUMAN,
                action_params={"reason": "low_match_confidence", "confidence": match_confidence},
                confidence=match_confidence,
            )
        
        if context["validation"] is None:
            return Thought(
                step=step,
                reasoning="검증을 수행합니다.",
                action=AgentAction.VALIDATE,
                action_params={
                    "parsed": context["parsed"],
                    "matches": context["matches"],
                    "diagnostic_answers": context["diagnostic_answers"],
                },
            )
        
        # 검증 완료, 최종 결과 반환
        return Thought(
            step=step,
            reasoning="모든 단계가 완료되었습니다. 결과를 반환합니다.",
            action=AgentAction.COMPLETE,
            confidence=self._calculate_overall_confidence(context),
        )
    
    def _get_llm_reasoning(self, context: Dict[str, Any], confidence: float) -> str:
        """LLM을 사용해 현재 상황 분석 및 추론."""
        if not self.use_llm_reasoning:
            return f"신뢰도: {confidence:.2f}"
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # 현재 상황 요약
            matches = context.get("matches", {}).get("matches", [])
            unmapped = [m["source"] for m in matches if m.get("unmapped")]
            low_conf = [m["source"] for m in matches if m.get("confidence", 1) < 0.7 and not m.get("unmapped")]
            
            prompt = f"""당신은 HR 데이터 검증 AI 에이전트입니다. 현재 상황을 분석하세요.

현재 상황:
- 매칭 신뢰도: {confidence:.2f}
- 미매핑 헤더: {unmapped[:5]}
- 낮은 신뢰도 헤더: {low_conf[:5]}
- 재시도 횟수: {self.retry_count}/2

다음 중 하나를 선택하고 이유를 1-2문장으로 설명하세요:
1. 재시도 (다른 전략으로 매칭 시도)
2. 사람에게 질문 (어떤 헤더가 어떤 필드인지 확인)
3. 진행 (현재 상태로 계속)

응답 형식: [선택번호] 이유"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",  # 빠르고 저렴한 모델
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"LLM 추론 실패: {e}. 규칙 기반 결정 사용."
    
    def _act(self, thought: Thought, context: Dict[str, Any]) -> Observation:
        """도구 실행."""
        try:
            if thought.action == AgentAction.PARSE:
                result = self.registry.call_tool("parse_roster", **thought.action_params)
                return Observation(
                    action=thought.action,
                    success=bool(result.get("headers")),
                    result=result,
                    confidence=1.0 if result.get("headers") else 0.0,
                )
            
            elif thought.action == AgentAction.MATCH:
                result = self.registry.call_tool("match_headers", **thought.action_params)
                confidence = self._calculate_match_confidence(result)
                return Observation(
                    action=thought.action,
                    success=True,
                    result=result,
                    confidence=confidence,
                )
            
            elif thought.action == AgentAction.VALIDATE:
                result = self.registry.call_tool("validate", **thought.action_params)
                confidence = self._calculate_validation_confidence(result)
                return Observation(
                    action=thought.action,
                    success=result.get("passed", False),
                    result=result,
                    confidence=confidence,
                )
            
            else:
                return Observation(
                    action=thought.action,
                    success=False,
                    result=None,
                    error=f"Unknown action: {thought.action}",
                )
        
        except Exception as e:
            return Observation(
                action=thought.action,
                success=False,
                result=None,
                error=str(e),
                confidence=0.0,
            )
    
    def _observe(self, observation: Observation, context: Dict[str, Any], action: AgentAction):
        """결과를 컨텍스트에 반영."""
        if not observation.success:
            return
        
        if action == AgentAction.PARSE:
            context["parsed"] = observation.result
        elif action == AgentAction.MATCH:
            context["matches"] = observation.result
        elif action == AgentAction.VALIDATE:
            context["validation"] = observation.result
    
    def _calculate_match_confidence(self, matches: Dict[str, Any]) -> float:
        """매칭 신뢰도 계산."""
        if matches is None:
            return 0.0
        
        match_list = matches.get("matches", [])
        if not match_list:
            return 0.0
        
        total_conf = sum(m.get("confidence", 0) for m in match_list)
        avg_conf = total_conf / len(match_list)
        
        # unmapped 패널티
        unmapped_count = sum(1 for m in match_list if m.get("unmapped"))
        unmapped_penalty = unmapped_count * 0.05
        
        return max(0.0, min(1.0, avg_conf - unmapped_penalty))
    
    def _calculate_validation_confidence(self, validation: Dict[str, Any]) -> float:
        """검증 신뢰도 계산."""
        if validation is None:
            return 0.0
        
        if validation.get("passed"):
            return 1.0
        
        errors = len(validation.get("errors", []))
        warnings = len(validation.get("warnings", []))
        
        confidence = 1.0 - (errors * 0.1) - (warnings * 0.05)
        return max(0.0, min(1.0, confidence))
    
    def _calculate_overall_confidence(self, context: Dict[str, Any]) -> float:
        """전체 신뢰도 계산."""
        match_conf = self._calculate_match_confidence(context.get("matches", {}))
        val_conf = self._calculate_validation_confidence(context.get("validation", {}))
        
        # 가중 평균
        return (match_conf * 0.4) + (val_conf * 0.6)
    
    def _build_final_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """최종 결과 구성."""
        overall_confidence = self._calculate_overall_confidence(context)
        
        # 신뢰도 등급
        if overall_confidence >= self.CONFIDENCE_AUTO_COMPLETE:
            grade = "A"
            recommendation = "auto_complete"
        elif overall_confidence >= self.CONFIDENCE_AUTO_CORRECT:
            grade = "B"
            recommendation = "auto_correct_with_review"
        elif overall_confidence >= self.CONFIDENCE_NEEDS_REVIEW:
            grade = "C"
            recommendation = "manual_review"
        else:
            grade = "D"
            recommendation = "full_manual_review"
        
        return {
            "status": self.state.status,
            "confidence": {
                "score": overall_confidence,
                "grade": grade,
                "recommendation": recommendation,
            },
            "steps": {
                "parsed_summary": {
                    "headers": (context.get("parsed") or {}).get("headers", []),
                    "row_count": len((context.get("parsed") or {}).get("rows", [])),
                },
                "matches": context.get("matches"),
                "validation": context.get("validation"),
            },
            "agent_reasoning": self.state.get_history(),
            "iterations": self.state.current_step,
            "needs_human_review": self.state.status == "needs_human",
        }
    
    def explain_reasoning(self) -> str:
        """추론 과정 설명 (사용자용)."""
        lines = ["🤖 AI 에이전트 추론 과정:\n"]
        
        for thought in self.state.thoughts:
            status = "⏳"
            if thought.action == AgentAction.COMPLETE:
                status = "✅"
            elif thought.action == AgentAction.FAIL:
                status = "❌"
            elif thought.action == AgentAction.ASK_HUMAN:
                status = "🙋"
            
            lines.append(f"{status} Step {thought.step}: {thought.reasoning}")
        
        return "\n".join(lines)


def create_react_agent(tool_registry, llm_client=None, verbose: bool = False) -> ReactAgent:
    """ReACT 에이전트 생성."""
    return ReactAgent(
        tool_registry=tool_registry,
        llm_client=llm_client,
        max_iterations=5,
        verbose=verbose,
    )
