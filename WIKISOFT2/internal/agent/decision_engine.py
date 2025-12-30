"""
Decision Engine: 자동 의사결정

신뢰도 기반으로 자동 의사결정을 수행합니다:
- 자동 완료 (신뢰도 95%+)
- 사람에게 문의 (신뢰도 50-95%)
- 거부 (신뢰도 <50%)
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import json


class DecisionType(str, Enum):
    """의사결정 유형"""
    AUTO_COMPLETE = "auto_complete"
    ASK_HUMAN = "ask_human"
    REJECT = "reject"
    ESCALATE = "escalate"


class DecisionReason(str, Enum):
    """의사결정 사유"""
    HIGH_CONFIDENCE = "high_confidence"
    MODERATE_CONFIDENCE = "moderate_confidence"
    LOW_CONFIDENCE = "low_confidence"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    EXECUTION_ERROR = "execution_error"
    ANOMALY_DETECTED = "anomaly_detected"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class Decision:
    """의사결정 기록"""
    type: DecisionType
    reason: DecisionReason
    confidence: float
    message: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "type": self.type.value,
            "reason": self.reason.value,
            "confidence": self.confidence,
            "message": self.message,
            "metadata": self.metadata or {},
        }


class DecisionEngine:
    """
    자동 의사결정 엔진
    
    신뢰도와 정책에 기반하여 자동 의사결정을 수행합니다.
    """
    
    def __init__(self):
        self.thresholds = {
            "auto_complete": 0.85,      # 85% 이상: 자동 완료
            "ask_human": 0.50,          # 50-85%: 사람에게 물음
            "reject": 0.0,              # 50% 미만: 거부
        }
        self.decisions: List[Decision] = []
        
        # 정책 규칙들
        self.policies = {
            "max_salary_change": 0.2,   # 급여 변화 최대 20%
            "min_headcount": 1,         # 최소 인원 1명
            "max_headcount": 10000,     # 최대 인원 10000명
        }
    
    async def decide(
        self,
        confidence: float,
        data: Dict[str, Any],
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        자동 의사결정 수행
        
        Args:
            confidence: 신뢰도 (0~1)
            data: 입력 데이터
            result: 처리 결과
            context: 추가 컨텍스트
        
        Returns:
            Decision
        """
        context = context or {}
        
        # 1. 데이터 품질 검사
        quality_check = self._check_data_quality(data)
        if not quality_check["pass"]:
            return Decision(
                type=DecisionType.ASK_HUMAN,
                reason=DecisionReason.DATA_QUALITY_ISSUE,
                confidence=confidence,
                message=f"Data quality issue: {quality_check['reason']}",
                metadata={"quality_check": quality_check},
            )
        
        # 2. 정책 위반 검사
        policy_check = self._check_policies(data, result)
        if not policy_check["pass"]:
            return Decision(
                type=DecisionType.ASK_HUMAN,
                reason=DecisionReason.POLICY_VIOLATION,
                confidence=confidence,
                message=f"Policy violation: {policy_check['reason']}",
                metadata={"policy_check": policy_check},
            )
        
        # 3. 이상치 탐지
        anomaly_check = self._check_anomalies(data, result)
        if anomaly_check["detected"]:
            confidence *= 0.8  # 신뢰도 20% 감소
        
        # 4. 신뢰도 기반 의사결정
        decision = self._decide_by_confidence(confidence, data, result)
        
        self.decisions.append(decision)
        return decision
    
    def _check_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 품질 검사
        
        Returns:
            {
                "pass": bool,
                "reason": str,
                "issues": [str, ...],
            }
        """
        issues = []
        
        # 필수 필드 확인
        required_fields = ["employee_type", "salary", "count"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            issues.append(f"Missing fields: {missing_fields}")
        
        # 데이터 타입 확인
        if "salary" in data:
            try:
                float(data["salary"])
            except (ValueError, TypeError):
                issues.append(f"Invalid salary: {data['salary']}")
        
        if "count" in data:
            try:
                int(data["count"])
            except (ValueError, TypeError):
                issues.append(f"Invalid count: {data['count']}")
        
        # NULL 값 확인
        null_fields = [k for k, v in data.items() if v is None or v == ""]
        if len(null_fields) > len(data) * 0.3:
            issues.append(f"Too many null values: {null_fields}")
        
        return {
            "pass": len(issues) == 0,
            "reason": "; ".join(issues) if issues else "OK",
            "issues": issues,
        }
    
    def _check_policies(
        self,
        data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        정책 위반 검사
        
        Returns:
            {
                "pass": bool,
                "reason": str,
                "violations": [str, ...],
            }
        """
        violations = []
        
        # 급여 범위 검사
        if "salary" in data and "previous_salary" in data:
            try:
                salary = float(data.get("salary", 0))
                prev_salary = float(data.get("previous_salary", salary))
                
                if prev_salary > 0:
                    change_rate = abs(salary - prev_salary) / prev_salary
                    if change_rate > self.policies["max_salary_change"]:
                        violations.append(
                            f"Salary change too large: {change_rate:.1%} "
                            f"(max: {self.policies['max_salary_change']:.1%})"
                        )
            except (ValueError, TypeError):
                pass
        
        # 인원 범위 검사
        if "count" in data:
            try:
                count = int(data.get("count", 0))
                if count < self.policies["min_headcount"]:
                    violations.append(f"Count too low: {count}")
                elif count > self.policies["max_headcount"]:
                    violations.append(f"Count too high: {count}")
            except (ValueError, TypeError):
                pass
        
        return {
            "pass": len(violations) == 0,
            "reason": "; ".join(violations) if violations else "OK",
            "violations": violations,
        }
    
    def _check_anomalies(
        self,
        data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이상치 탐지
        
        Returns:
            {
                "detected": bool,
                "anomalies": [str, ...],
            }
        """
        anomalies = []
        
        # 미래 날짜 검사
        if "date" in data:
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(str(data["date"]))
                if date_obj > datetime.now():
                    anomalies.append(f"Future date detected: {data['date']}")
            except (ValueError, TypeError):
                pass
        
        # 비정상적인 조합
        if data.get("employee_type") == "retired" and data.get("salary", 0) > 0:
            anomalies.append("Retired employee with salary")
        
        return {
            "detected": len(anomalies) > 0,
            "anomalies": anomalies,
        }
    
    def _decide_by_confidence(
        self,
        confidence: float,
        data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Decision:
        """신뢰도 기반 의사결정"""
        
        if confidence >= self.thresholds["auto_complete"]:
            return Decision(
                type=DecisionType.AUTO_COMPLETE,
                reason=DecisionReason.HIGH_CONFIDENCE,
                confidence=confidence,
                message=f"자동 완료 (신뢰도: {confidence:.1%})",
                metadata={"threshold": self.thresholds["auto_complete"]},
            )
        
        elif confidence >= self.thresholds["ask_human"]:
            return Decision(
                type=DecisionType.ASK_HUMAN,
                reason=DecisionReason.MODERATE_CONFIDENCE,
                confidence=confidence,
                message=f"사람의 검토 필요 (신뢰도: {confidence:.1%})",
                metadata={"threshold": self.thresholds["ask_human"]},
            )
        
        else:
            return Decision(
                type=DecisionType.REJECT,
                reason=DecisionReason.LOW_CONFIDENCE,
                confidence=confidence,
                message=f"신뢰도 부족으로 거부 (신뢰도: {confidence:.1%})",
                metadata={"threshold": self.thresholds["reject"]},
            )
    
    def set_threshold(self, decision_type: DecisionType, threshold: float) -> None:
        """의사결정 임계값 조정"""
        if decision_type == DecisionType.AUTO_COMPLETE:
            self.thresholds["auto_complete"] = threshold
        elif decision_type == DecisionType.ASK_HUMAN:
            self.thresholds["ask_human"] = threshold
        elif decision_type == DecisionType.REJECT:
            self.thresholds["reject"] = threshold
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """의사결정 통계"""
        if not self.decisions:
            return {
                "total": 0,
                "auto_complete": 0,
                "ask_human": 0,
                "reject": 0,
                "average_confidence": 0,
            }
        
        decision_counts = {}
        for dt in DecisionType:
            count = sum(1 for d in self.decisions if d.type == dt)
            decision_counts[dt.value] = count
        
        confidence_scores = [d.confidence for d in self.decisions]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            "total": len(self.decisions),
            "auto_complete": decision_counts.get(DecisionType.AUTO_COMPLETE.value, 0),
            "ask_human": decision_counts.get(DecisionType.ASK_HUMAN.value, 0),
            "reject": decision_counts.get(DecisionType.REJECT.value, 0),
            "escalate": decision_counts.get(DecisionType.ESCALATE.value, 0),
            "average_confidence": round(avg_confidence, 3),
        }
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """의사결정 이력"""
        return [d.to_dict() for d in self.decisions]
