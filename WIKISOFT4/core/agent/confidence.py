"""
정상 데이터 비율 계산 & 이상치 감지
"""
from typing import Any, Dict

from core.validators.validation_layer1 import validate_layer1
from core.validators.validation_layer2 import validate_layer2


def estimate_confidence(parsed: Dict[str, Any], matches: Dict[str, Any], validation_l1: Dict[str, Any]) -> Dict[str, Any]:
    """정상 데이터 비율 계산: 0.0~1.0 범위.

    계산 방식:
    - 전체 행 수 대비 에러가 없는 행의 비율
    - 에러가 있는 행을 제외한 비율 = 정상 데이터 비율
    """
    total_rows = len(parsed.get("rows", []))
    if total_rows == 0:
        return {
            "score": 1.0,
            "label": "정상 데이터 비율",
            "factors": {
                "total_rows": 0,
                "error_rows": 0,
                "warning_rows": 0,
            },
        }

    # 에러/경고가 있는 행 수 계산
    errors = validation_l1.get("errors", []) if isinstance(validation_l1, dict) else []
    warnings = validation_l1.get("warnings", []) if isinstance(validation_l1, dict) else []
    
    error_rows = set(e.get("row") for e in errors if "row" in e)
    warning_rows = set(w.get("row") for w in warnings if "row" in w)
    
    # 정상 행 = 전체 - 에러 행
    normal_rows = total_rows - len(error_rows)
    score = normal_rows / total_rows if total_rows > 0 else 1.0

    return {
        "score": max(0.0, min(1.0, score)),
        "label": "정상 데이터 비율",
        "factors": {
            "total_rows": total_rows,
            "error_rows": len(error_rows),
            "warning_rows": len(warning_rows),
            "normal_rows": normal_rows,
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

    # matches가 리스트인 경우 처리
    if isinstance(matches, list):
        match_list = matches
    else:
        match_list = matches.get("matches", [])

    # unmapped 헤더 비율
    unmapped_count = sum(1 for m in match_list if m.get("unmapped"))
    if match_list and unmapped_count / len(match_list) > 0.2:
        anomalies.append({
            "type": "high_unmapped_headers",
            "severity": "warning",
            "message": f"매핑되지 않은 컬럼이 20% 초과 ({unmapped_count}/{len(match_list)}개)",
        })

    # L1 에러 비율 - 개별 에러가 이미 표시되므로 제거 (중복 방지)
    # errors = validation_l1.get("errors", [])
    # ...

    # 낮은 매칭 신뢰도
    if match_list:
        avg_conf = sum(m.get("confidence", 0) for m in match_list) / len(match_list)
        if avg_conf < 0.5:
            anomalies.append({
                "type": "low_match_confidence",
                "severity": "warning",
                "message": f"헤더 매칭 신뢰도가 낮음 (평균 {avg_conf:.0%})",
            })

    return {
        "detected": len(anomalies) > 0,
        "anomalies": anomalies,
        "recommendation": "manual_review" if anomalies else "auto_proceed",
    }
