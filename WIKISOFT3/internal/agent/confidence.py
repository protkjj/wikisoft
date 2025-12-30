"""
Confidence & Anomaly 감지: 간단한 휴리스틱 기반 규칙
"""
from typing import Any, Dict

from internal.validators.validation_layer1 import validate_layer1
from internal.validators.validation_layer2 import validate_layer2


def estimate_confidence(parsed: Dict[str, Any], matches: Dict[str, Any], validation_l1: Dict[str, Any]) -> Dict[str, Any]:
    """신뢰도 추정: 0.0~1.0 범위.

    규칙:
    - 매칭 신뢰도 평균: 0~1.0
    - L1 에러 패널티: 각 에러당 -0.1
    - 경고 패널티: 각 경고당 -0.05
    - 최소: 0.0, 최대: 1.0
    """
    confidence = 1.0

    # 매칭 신뢰도
    match_list = matches.get("matches", [])
    if match_list:
        avg_conf = sum(m.get("confidence", 0) for m in match_list) / len(match_list)
        confidence *= avg_conf

    # L1 검증 페널티
    errors = validation_l1.get("errors", [])
    warnings = validation_l1.get("warnings", [])
    confidence -= len(errors) * 0.1
    confidence -= len(warnings) * 0.05

    return {
        "score": max(0.0, min(1.0, confidence)),
        "factors": {
            "match_confidence": avg_conf if match_list else 0.0,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }


def detect_anomalies(parsed: Dict[str, Any], matches: Dict[str, Any], validation_l1: Dict[str, Any]) -> Dict[str, Any]:
    """이상치 감지: 간단한 규칙 기반.

    감지 항목:
    - unmapped 헤더 > 20%
    - L1 에러 > 5%
    - 매칭 신뢰도 < 0.5
    """
    import pandas as pd

    anomalies = []

    # unmapped 헤더 비율
    match_list = matches.get("matches", [])
    unmapped_count = sum(1 for m in match_list if m.get("unmapped"))
    if match_list and unmapped_count / len(match_list) > 0.2:
        anomalies.append({
            "type": "high_unmapped_headers",
            "severity": "warning",
            "message": f"Unmapped headers > 20% ({unmapped_count}/{len(match_list)})",
        })

    # L1 에러 비율
    errors = validation_l1.get("errors", [])
    if "rows" in parsed and len(parsed["rows"]) > 0:
        error_rows = {e.get("row") for e in errors if "row" in e}
        error_rate = len(error_rows) / len(parsed["rows"])
        if error_rate > 0.05:
            anomalies.append({
                "type": "high_error_rate",
                "severity": "error",
                "message": f"Error rate > 5% ({len(error_rows)}/{len(parsed['rows'])})",
            })

    # 낮은 매칭 신뢰도
    if match_list:
        avg_conf = sum(m.get("confidence", 0) for m in match_list) / len(match_list)
        if avg_conf < 0.5:
            anomalies.append({
                "type": "low_match_confidence",
                "severity": "warning",
                "message": f"Average match confidence < 0.5 ({avg_conf:.2f})",
            })

    return {
        "detected": len(anomalies) > 0,
        "anomalies": anomalies,
        "recommendation": "manual_review" if anomalies else "auto_proceed",
    }
