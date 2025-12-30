"""
동적 질문 생성기

이상치 감지 결과를 기반으로 추가 질문을 자동 생성합니다.
- unmapped 헤더에 대한 질문
- 데이터 이상치에 대한 확인 질문
- AI가 확인이 필요하다고 판단한 항목
"""
from typing import Any, Dict, List, Optional
import os

from internal.ai.llm_client import chat


def generate_dynamic_questions(
    anomalies: Dict[str, Any],
    matches: Dict[str, Any],
    validation: Dict[str, Any],
    max_questions: int = 5
) -> List[Dict[str, Any]]:
    """
    검증 결과를 기반으로 동적 질문 생성
    
    Args:
        anomalies: 이상 탐지 결과
        matches: 헤더 매칭 결과
        validation: 검증 결과
        max_questions: 최대 질문 수
    
    Returns:
        생성된 질문 리스트
    """
    questions = []
    
    # 1. Unmapped 헤더에 대한 질문
    unmapped_questions = _generate_unmapped_questions(matches)
    questions.extend(unmapped_questions[:2])  # 최대 2개
    
    # 2. 이상치에 대한 질문
    anomaly_questions = _generate_anomaly_questions(anomalies)
    questions.extend(anomaly_questions[:2])  # 최대 2개
    
    # 3. AI 기반 추가 질문 (위에서 부족하면)
    if len(questions) < max_questions:
        ai_questions = _generate_ai_questions(
            anomalies, matches, validation,
            existing_count=len(questions),
            max_count=max_questions - len(questions)
        )
        questions.extend(ai_questions)
    
    # 질문 ID 부여
    for i, q in enumerate(questions[:max_questions]):
        q["id"] = f"dq_{i + 1}"
        q["dynamic"] = True
    
    return questions[:max_questions]


def _generate_unmapped_questions(matches: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Unmapped 헤더에 대한 질문 생성"""
    questions = []
    match_list = matches.get("matches", [])
    
    for match in match_list:
        if match.get("unmapped") or not match.get("target"):
            source_header = match.get("source", "")
            
            questions.append({
                "type": "unmapped_header",
                "severity": "warning",
                "question": f"'{source_header}' 컬럼의 의미를 알려주세요. 이 데이터는 어떤 용도로 사용되나요?",
                "context": {
                    "header": source_header,
                    "confidence": match.get("confidence", 0)
                },
                "options": [
                    {"value": "ignore", "label": "사용하지 않음 (무시)"},
                    {"value": "describe", "label": "직접 설명하기"},
                ]
            })
    
    return questions


def _generate_anomaly_questions(anomalies: Dict[str, Any]) -> List[Dict[str, Any]]:
    """이상치에 대한 질문 생성"""
    questions = []
    anomaly_list = anomalies.get("anomalies", [])
    
    for anomaly in anomaly_list:
        anomaly_type = anomaly.get("type", "")
        message = anomaly.get("message", "")
        severity = anomaly.get("severity", "warning")
        
        # 이미 질문 형태인 것은 그대로 사용
        if anomaly_type == "ai_question":
            questions.append({
                "type": "ai_question",
                "severity": "question",
                "question": message,
                "options": [
                    {"value": "yes", "label": "예"},
                    {"value": "no", "label": "아니오"},
                    {"value": "explain", "label": "설명 필요"},
                ]
            })
            continue
        
        # 이상치 유형별 질문 생성
        if anomaly_type == "high_unmapped_headers":
            questions.append({
                "type": "confirmation",
                "severity": severity,
                "question": f"매칭되지 않은 헤더가 많습니다. {message} 이 파일 형식이 맞는지 확인해주세요.",
                "options": [
                    {"value": "correct", "label": "맞습니다"},
                    {"value": "wrong", "label": "다른 파일입니다"},
                ]
            })
        
        elif anomaly_type == "high_error_rate":
            questions.append({
                "type": "confirmation",
                "severity": "error",
                "question": f"데이터 오류율이 높습니다. {message} 데이터를 다시 확인해주시겠습니까?",
                "options": [
                    {"value": "recheck", "label": "다시 확인하겠습니다"},
                    {"value": "proceed", "label": "그대로 진행"},
                ]
            })
        
        elif anomaly_type == "headcount_mismatch":
            questions.append({
                "type": "confirmation",
                "severity": severity,
                "question": message + " 진단 답변과 명부 데이터 중 어느 것이 맞나요?",
                "options": [
                    {"value": "answer", "label": "진단 답변이 맞습니다"},
                    {"value": "data", "label": "명부 데이터가 맞습니다"},
                    {"value": "check", "label": "확인이 필요합니다"},
                ]
            })
    
    return questions


def _generate_ai_questions(
    anomalies: Dict[str, Any],
    matches: Dict[str, Any],
    validation: Dict[str, Any],
    existing_count: int,
    max_count: int
) -> List[Dict[str, Any]]:
    """AI를 사용한 추가 질문 생성"""
    if max_count <= 0:
        return []
    
    # AI가 없으면 빈 리스트 반환
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []
    
    try:
        # 컨텍스트 요약
        context_summary = {
            "anomalies": anomalies.get("anomalies", [])[:5],
            "unmapped_count": sum(1 for m in matches.get("matches", []) if m.get("unmapped")),
            "total_headers": len(matches.get("matches", [])),
            "validation_passed": validation.get("passed", False),
            "error_count": len(validation.get("errors", [])),
            "warning_count": len(validation.get("warnings", []))
        }
        
        prompt = f"""당신은 퇴직급여채무 검증 전문가입니다.
아래 검증 결과를 보고, 고객에게 추가로 확인이 필요한 질문을 생성하세요.

## 검증 결과 요약:
{context_summary}

## 규칙:
1. 이미 {existing_count}개의 질문이 있음
2. 최대 {max_count}개의 추가 질문만 생성
3. 정말 확인이 필요한 것만 질문
4. 질문은 명확하고 구체적이어야 함

## 응답 형식 (JSON만):
{{
  "questions": [
    {{
      "question": "질문 내용",
      "reason": "이 질문이 필요한 이유"
    }}
  ]
}}

추가 질문이 필요 없으면 빈 배열을 반환하세요.
JSON만 출력하세요."""

        response = chat(prompt)
        
        import json
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        questions = []
        for q in result.get("questions", [])[:max_count]:
            questions.append({
                "type": "ai_generated",
                "severity": "question",
                "question": q.get("question", ""),
                "reason": q.get("reason", ""),
                "options": [
                    {"value": "yes", "label": "예"},
                    {"value": "no", "label": "아니오"},
                    {"value": "explain", "label": "설명하기"},
                ]
            })
        
        return questions
        
    except Exception as e:
        print(f"AI 질문 생성 실패: {e}")
        return []


def format_questions_for_ui(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """UI에서 사용하기 좋은 형태로 질문 포맷팅"""
    formatted = []
    
    for q in questions:
        formatted.append({
            "id": q.get("id", ""),
            "question": q.get("question", ""),
            "type": q.get("type", "confirmation"),
            "severity": q.get("severity", "info"),
            "options": q.get("options", []),
            "dynamic": q.get("dynamic", True),
            "required": q.get("severity") == "error"
        })
    
    return formatted
