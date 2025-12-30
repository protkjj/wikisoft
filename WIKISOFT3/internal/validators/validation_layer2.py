"""
Layer 2 검증: 챗봇 답변 vs 명부 자동계산 비교 - v2에서 이식
"""
from typing import Any, Dict, List, Optional

from internal.ai.diagnostic_questions import get_validation_questions


def validate_layer2(chatbot_answers: Dict[str, Any], calculated_aggregates: Dict[str, Any], tolerance_percent: float = 5.0) -> Dict[str, Any]:
    """Layer 2: 챗봇 답변과 자동 계산된 집계값 비교."""
    # 퇴직자 전체 자동 계산
    if all(k in chatbot_answers for k in ["q24", "q25", "q26"]):
        chatbot_answers["퇴직자전체"] = float(chatbot_answers["q24"]) + float(chatbot_answers["q25"]) + float(chatbot_answers["q26"])

    validation_questions = get_validation_questions()
    results = {"status": "passed", "total_checks": 0, "passed": 0, "warnings": []}

    for question in validation_questions:
        qid = question["id"]
        user_answer = chatbot_answers.get(qid)
        if user_answer is None:
            continue

        results["total_checks"] += 1
        validate_path = question.get("validate_against")
        calculated_value = _extract_value(calculated_aggregates, validate_path) if validate_path else None

        if calculated_value is None:
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_answer,
                "calculated": None,
                "severity": "info",
                "message": "명부에서 이 값을 자동 계산할 수 없습니다.",
            })
            continue

        try:
            user_value = float(user_answer)
            calc_value = float(calculated_value)
        except (ValueError, TypeError):
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_answer,
                "calculated": calculated_value,
                "severity": "error",
                "message": "숫자 형식이 올바르지 않습니다.",
            })
            continue

        diff = user_value - calc_value
        diff_percent = abs(diff / calc_value * 100) if calc_value != 0 else float("inf")

        if abs(diff) < 0.01:
            results["passed"] += 1
        elif diff_percent <= tolerance_percent:
            results["passed"] += 1
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_value,
                "calculated": calc_value,
                "diff_percent": round(diff_percent, 1),
                "severity": "low",
                "message": f"경미한 차이 ({diff_percent:.1f}%)",
            })
        else:
            results["warnings"].append({
                "question_id": qid,
                "question": question["question"],
                "user_input": user_value,
                "calculated": calc_value,
                "diff_percent": round(diff_percent, 1),
                "severity": "high",
                "message": f"⭕ 명부: {calc_value}, 입력: {user_value} (차이: {diff_percent:.1f}%)",
            })

    high_warnings = [w for w in results["warnings"] if w.get("severity") == "high"]
    if high_warnings:
        results["status"] = "failed"
    elif results["warnings"]:
        results["status"] = "warnings"

    return results


def _extract_value(data: Dict[str, Any], path: Optional[str]) -> Optional[float]:
    if not path or not data:
        return None
    try:
        if "[" in path:
            key, index_str = path.split("[")
            index = int(index_str.rstrip("]"))
            return data[key][index]
        return data[path]
    except (KeyError, IndexError, ValueError, TypeError):
        return None
