"""
자율 학습 시스템: 고객 행동에서 패턴을 감지하고 자동 학습
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from internal.ai.llm_client import LLMClient
from internal.ai.knowledge_base import add_error_rule, learn_from_correction, load_learned_patterns


# 행동 로그 저장 경로
BEHAVIOR_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "training_data",
    "behavior_logs.json"
)


def log_customer_behavior(
    action: str,
    context: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    고객 행동 로깅.
    
    Actions:
    - "error_ignored": 오류를 확인했지만 수정 안 함
    - "file_resubmitted": 파일 재제출 (오류 수정됨)
    - "chat_clarification": 챗봇에서 오류 관련 질문
    - "mapping_confirmed": 매핑 확인 후 진행
    - "mapping_changed": 매핑 수동 변경
    """
    # 로그 파일 로드
    if os.path.exists(BEHAVIOR_LOG_PATH):
        with open(BEHAVIOR_LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = {"events": [], "patterns_analyzed": 0}
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "context": context,
        "session_id": session_id,
        "analyzed": False
    }
    
    logs["events"].append(event)
    
    # 저장
    os.makedirs(os.path.dirname(BEHAVIOR_LOG_PATH), exist_ok=True)
    with open(BEHAVIOR_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    
    # 일정 이벤트 수 이상이면 자동 분석 트리거
    unanalyzed = sum(1 for e in logs["events"] if not e.get("analyzed", False))
    if unanalyzed >= 10:
        analyze_and_learn()


def analyze_and_learn() -> Dict[str, Any]:
    """
    축적된 행동 로그를 분석하고 패턴 학습.
    AI가 자율적으로 판단.
    """
    if not os.path.exists(BEHAVIOR_LOG_PATH):
        return {"status": "no_logs"}
    
    with open(BEHAVIOR_LOG_PATH, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    events = [e for e in logs.get("events", []) if not e.get("analyzed", False)]
    
    if len(events) < 5:
        return {"status": "insufficient_data", "count": len(events)}
    
    # 패턴 분석
    patterns = _extract_patterns(events)
    
    if not patterns:
        # 모든 이벤트를 analyzed로 표시
        for e in logs["events"]:
            e["analyzed"] = True
        with open(BEHAVIOR_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return {"status": "no_patterns"}
    
    # AI에게 학습 여부 판단 요청
    learned = _ai_decide_learning(patterns)
    
    # 분석 완료 표시
    for e in logs["events"]:
        e["analyzed"] = True
    logs["patterns_analyzed"] = logs.get("patterns_analyzed", 0) + 1
    
    with open(BEHAVIOR_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    
    return {
        "status": "analyzed",
        "patterns_found": len(patterns),
        "rules_learned": len(learned)
    }


def _extract_patterns(events: List[Dict]) -> List[Dict]:
    """이벤트에서 반복 패턴 추출"""
    patterns = []
    
    # 1. 같은 오류를 여러 번 무시한 패턴
    ignored_errors = defaultdict(list)
    for e in events:
        if e["action"] == "error_ignored":
            ctx = e.get("context", {})
            key = (ctx.get("field"), ctx.get("error_type"))
            ignored_errors[key].append(e)
    
    for (field, error_type), occurrences in ignored_errors.items():
        if len(occurrences) >= 3:
            patterns.append({
                "type": "repeated_ignore",
                "field": field,
                "error_type": error_type,
                "count": len(occurrences),
                "contexts": [o.get("context", {}) for o in occurrences[:5]]
            })
    
    # 2. 챗봇에서 "오류 아님" 언급 패턴
    clarifications = [e for e in events if e["action"] == "chat_clarification"]
    for c in clarifications:
        msg = c.get("context", {}).get("message", "").lower()
        if any(kw in msg for kw in ["오류 아님", "정상", "괜찮", "문제없", "무시해"]):
            patterns.append({
                "type": "chat_not_error",
                "field": c.get("context", {}).get("field"),
                "message": c.get("context", {}).get("message"),
                "diagnostic_context": c.get("context", {}).get("diagnostic_context")
            })
    
    # 3. 매핑 변경 패턴 (같은 헤더가 반복적으로 다르게 매핑)
    mapping_changes = defaultdict(list)
    for e in events:
        if e["action"] == "mapping_changed":
            ctx = e.get("context", {})
            source = ctx.get("source_header")
            mapping_changes[source].append(ctx.get("new_target"))
    
    for source, targets in mapping_changes.items():
        if len(targets) >= 2:
            # 가장 많이 선택된 타겟
            most_common = max(set(targets), key=targets.count)
            patterns.append({
                "type": "mapping_preference",
                "source_header": source,
                "preferred_target": most_common,
                "count": targets.count(most_common)
            })
    
    return patterns


def _ai_decide_learning(patterns: List[Dict]) -> List[str]:
    """AI가 패턴을 보고 학습 여부 결정"""
    if not patterns:
        return []
    
    # 기존 학습된 패턴 로드
    existing = load_learned_patterns()
    existing_keys = set()
    for p in existing:
        # field + interpretation 조합으로 중복 체크 (더 엄격)
        key = (p.get("field"), p.get("correct_interpretation", "")[:30])
        existing_keys.add(key)
    
    learned = []
    
    try:
        client = LLMClient()
        
        prompt = f"""당신은 HR 데이터 검증 시스템의 학습 관리자입니다.
아래 고객 행동 패턴을 분석하고, 새로운 규칙으로 학습해야 할지 결정하세요.

=== 발견된 패턴 ===
{json.dumps(patterns, ensure_ascii=False, indent=2)}

=== 기존 학습된 패턴 수 ===
{len(existing)}개

=== 판단 기준 ===
1. 같은 오류를 3번 이상 무시했다면 → 예외 패턴일 가능성 높음
2. 챗봇에서 "정상"이라고 명시적으로 말했다면 → 학습
3. 이미 비슷한 패턴이 학습되어 있다면 → 스킵
4. 컨텍스트(종업원구분, 회사 특성)가 명확하면 → 학습

JSON 형식으로 응답하세요:
{{
    "decisions": [
        {{
            "pattern_index": 0,
            "should_learn": true/false,
            "reason": "학습/스킵 이유",
            "rule_to_add": {{
                "field": "필드명",
                "interpretation": "해석",
                "context": {{"key": "value"}}
            }}
        }}
    ]
}}
"""
        
        response = client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1500
        )
        
        # JSON 파싱
        result = _parse_json_response(response)
        
        if result and "decisions" in result:
            for decision in result["decisions"]:
                if decision.get("should_learn"):
                    rule = decision.get("rule_to_add", {})
                    field = rule.get("field")
                    interpretation = rule.get("interpretation")
                    context = rule.get("context", {})
                    
                    if field and interpretation:
                        # 중복 체크 (field + interpretation 앞 30자)
                        check_key = (field, interpretation[:30])
                        if check_key not in existing_keys:
                            learn_from_correction(
                                field=field,
                                original_value="auto_learned",
                                was_error=True,
                                correct_interpretation=interpretation,
                                diagnostic_context=context
                            )
                            learned.append(f"{field}: {interpretation}")
                            # 동일 세션에서 중복 방지
                            existing_keys.add(check_key)
    
    except Exception as e:
        print(f"AI 학습 판단 오류: {e}")
    
    return learned


def _parse_json_response(response: str) -> Optional[Dict]:
    """AI 응답에서 JSON 추출"""
    try:
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        return json.loads(response)
    except:
        return None


# 챗봇 대화에서 자동 호출되는 함수
def analyze_chat_for_learning(
    user_message: str,
    ai_response: str,
    validation_context: Optional[Dict] = None
) -> None:
    """
    챗봇 대화에서 학습 가능한 패턴 감지.
    
    예: 사용자가 "65세 입사는 임원이라 정상이에요"라고 하면
        → 자동으로 패턴 학습
    """
    # 학습 트리거 키워드 (더 유연하게)
    not_error_keywords = [
        "오류 아님", "오류가 아님", "오류가 아닙니다", "오류 아닙니다",
        "정상", "괜찮", "문제없", "무시", "예외",
        "맞습니다", "맞아요", "에러 아님", "틀리지 않"
    ]
    
    # 한글은 lower() 불필요
    user_text = user_message
    
    if any(kw in user_text for kw in not_error_keywords):
        # 관련 필드 추출 시도
        field = None
        for f in ["입사연령", "생년월일", "기준급여", "성별", "입사일", "입사", "연령"]:
            if f in user_message or f in ai_response:
                field = f
                break
        
        # 필드를 못 찾았어도 로그
        if field is None:
            field = "알 수 없음"
        
        log_customer_behavior(
            action="chat_clarification",
            context={
                "field": field,
                "message": user_message,
                "ai_response": ai_response[:200] if ai_response else "",
                "diagnostic_context": validation_context
            }
        )


def get_learning_stats() -> Dict[str, Any]:
    """학습 시스템 통계"""
    stats = {
        "behavior_logs": 0,
        "unanalyzed_events": 0,
        "patterns_analyzed": 0,
        "learned_patterns": 0
    }
    
    if os.path.exists(BEHAVIOR_LOG_PATH):
        with open(BEHAVIOR_LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            stats["behavior_logs"] = len(logs.get("events", []))
            stats["unanalyzed_events"] = sum(
                1 for e in logs.get("events", []) 
                if not e.get("analyzed", False)
            )
            stats["patterns_analyzed"] = logs.get("patterns_analyzed", 0)
    
    patterns = load_learned_patterns()
    stats["learned_patterns"] = len(patterns)
    
    return stats
