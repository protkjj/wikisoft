"""
Confidence Calculator: 신뢰도 계산

의사결정 신뢰도를 다각적으로 평가합니다:
- Action 신뢰도
- Tool 신뢰도
- Data 신뢰도
- 결과 신뢰도
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import statistics


@dataclass
class ConfidenceScore:
    """신뢰도 점수"""
    overall: float        # 0.0 ~ 1.0
    action: float         # Action 선택 신뢰도
    tool: float          # Tool 실행 신뢰도
    data: float          # Input 데이터 신뢰도
    result: float        # 결과 신뢰도
    breakdown: Dict[str, float] = None


class ConfidenceCalculator:
    """
    신뢰도 계산기
    
    여러 신뢰도 지표를 조합하여 최종 신뢰도를 계산합니다.
    """
    
    def __init__(self):
        self.weights = {
            "action": 0.25,      # Action 선택 신뢰도
            "tool": 0.25,        # Tool 실행 신뢰도
            "data": 0.20,        # Data 품질 신뢰도
            "result": 0.30,      # 결과 신뢰도
        }
        self.history: List[ConfidenceScore] = []
    
    def calculate(
        self,
        action_confidence: float,
        tool_confidence: float,
        data_quality: float,
        result_confidence: float
    ) -> ConfidenceScore:
        """
        종합 신뢰도 계산
        
        Args:
            action_confidence: Action 선택 신뢰도 (0~1)
            tool_confidence: Tool 실행 신뢰도 (0~1)
            data_quality: 입력 데이터 품질 (0~1)
            result_confidence: 결과 신뢰도 (0~1)
        
        Returns:
            ConfidenceScore
        """
        # 각 신뢰도를 0-1 범위로 정규화
        action_conf = max(0.0, min(1.0, action_confidence))
        tool_conf = max(0.0, min(1.0, tool_confidence))
        data_conf = max(0.0, min(1.0, data_quality))
        result_conf = max(0.0, min(1.0, result_confidence))
        
        # 가중 평균으로 종합 신뢰도 계산
        overall = (
            action_conf * self.weights["action"] +
            tool_conf * self.weights["tool"] +
            data_conf * self.weights["data"] +
            result_conf * self.weights["result"]
        )
        
        score = ConfidenceScore(
            overall=round(overall, 3),
            action=round(action_conf, 3),
            tool=round(tool_conf, 3),
            data=round(data_conf, 3),
            result=round(result_conf, 3),
            breakdown={
                "action": round(action_conf * self.weights["action"], 3),
                "tool": round(tool_conf * self.weights["tool"], 3),
                "data": round(data_conf * self.weights["data"], 3),
                "result": round(result_conf * self.weights["result"], 3),
            }
        )
        
        self.history.append(score)
        return score
    
    def calculate_from_observations(
        self,
        observations: List[Dict[str, Any]]
    ) -> ConfidenceScore:
        """
        Observation 목록에서 신뢰도 계산
        
        Args:
            observations: Tool 실행 결과들
        
        Returns:
            ConfidenceScore
        """
        if not observations:
            return ConfidenceScore(overall=0.0, action=0.0, tool=0.0, data=0.0, result=0.0)
        
        # Tool 신뢰도: 성공률
        tool_success_count = sum(1 for o in observations if o.get("success", False))
        tool_conf = tool_success_count / len(observations)
        
        # 실행 시간 신뢰도: 빠를수록 높음
        execution_times = [o.get("execution_time", 1.0) for o in observations]
        avg_execution_time = statistics.mean(execution_times)
        time_conf = max(0.0, 1.0 - (avg_execution_time / 10.0))  # 10초 기준
        
        # 에러율 신뢰도
        error_count = sum(1 for o in observations if o.get("error"))
        error_conf = 1.0 - (error_count / len(observations)) if len(observations) > 0 else 0.0
        
        # 종합 도구 신뢰도
        tool_conf_final = (tool_conf * 0.5 + time_conf * 0.3 + error_conf * 0.2)
        
        return self.calculate(
            action_confidence=0.7,      # 기본값
            tool_confidence=tool_conf_final,
            data_quality=0.7,           # 기본값
            result_confidence=tool_conf,
        )
    
    def calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """
        데이터 품질 평가
        
        Args:
            data: 평가할 데이터
        
        Returns:
            신뢰도 (0~1)
        """
        if not data:
            return 0.0
        
        issues = 0
        checks = 0
        
        # 1. NULL/None 값 확인
        checks += 1
        none_count = sum(1 for v in data.values() if v is None)
        if none_count > len(data) * 0.1:
            issues += 1
        
        # 2. 데이터 타입 일관성
        checks += 1
        types = [type(v).__name__ for v in data.values()]
        if len(set(types)) > 1:
            issues += 0.5
        
        # 3. 값 범위 합리성
        checks += 1
        numeric_values = [v for v in data.values() if isinstance(v, (int, float))]
        if numeric_values:
            if any(v < 0 for v in numeric_values):
                issues += 0.3
        
        # 4. 데이터 크기
        checks += 1
        if len(data) == 0:
            issues += 1
        elif len(data) > 1000:
            issues += 0.2
        
        quality = max(0.0, (checks - issues) / checks)
        return round(quality, 3)
    
    def calculate_result_confidence(
        self,
        result: Dict[str, Any],
        expected_keys: List[str] = None
    ) -> float:
        """
        결과 신뢰도 평가
        
        Args:
            result: 실행 결과
            expected_keys: 기대되는 키들
        
        Returns:
            신뢰도 (0~1)
        """
        if not result:
            return 0.0
        
        confidence = 0.5  # 기본값
        
        # 1. 예상 키 포함 여부
        if expected_keys:
            found_keys = sum(1 for k in expected_keys if k in result)
            confidence += (found_keys / len(expected_keys)) * 0.3
        else:
            confidence += 0.3
        
        # 2. 에러 포함 여부
        if "error" in result and result["error"]:
            confidence -= 0.2
        
        # 3. Success 플래그
        if result.get("success", True):
            confidence += 0.2
        else:
            confidence -= 0.3
        
        return round(max(0.0, min(1.0, confidence)), 3)
    
    def should_ask_human(self, confidence: float, threshold: float = 0.7) -> bool:
        """
        사람에게 물어봐야 하는지 판단
        
        Args:
            confidence: 신뢰도 점수
            threshold: 판단 임계값
        
        Returns:
            True if confidence < threshold
        """
        return confidence < threshold
    
    def get_recommendation(self, confidence: float) -> Dict[str, Any]:
        """
        신뢰도에 따른 추천
        
        Args:
            confidence: 신뢰도 점수
        
        Returns:
            {
                "action": "auto_complete|ask_human|reject",
                "reason": str,
                "message": str,
            }
        """
        if confidence >= 0.95:
            return {
                "action": "auto_complete",
                "reason": "Very high confidence",
                "message": "자동으로 완료합니다 (신뢰도 95%+)",
            }
        elif confidence >= 0.85:
            return {
                "action": "auto_complete",
                "reason": "High confidence",
                "message": "자동으로 완료합니다 (신뢰도 85%+)",
            }
        elif confidence >= 0.70:
            return {
                "action": "ask_human",
                "reason": "Moderate confidence",
                "message": "검토 후 확인해주세요 (신뢰도 70%+)",
            }
        elif confidence >= 0.50:
            return {
                "action": "ask_human",
                "reason": "Low confidence",
                "message": "사람이 직접 확인하시기 바랍니다 (신뢰도 50%+)",
            }
        else:
            return {
                "action": "reject",
                "reason": "Very low confidence",
                "message": "신뢰도가 낮아 거부합니다 (신뢰도 <50%)",
            }
    
    def get_history(self) -> List[ConfidenceScore]:
        """신뢰도 계산 이력 조회"""
        return self.history
    
    def get_average_confidence(self) -> float:
        """평균 신뢰도"""
        if not self.history:
            return 0.0
        
        overall_scores = [s.overall for s in self.history]
        return round(statistics.mean(overall_scores), 3)
    
    def reset(self) -> None:
        """이력 초기화"""
        self.history.clear()
