"""
명부 데이터 집계 계산

엑셀 데이터에서 인원수, 금액 등을 자동 계산하여
Layer 2 검증에서 사용자 입력값과 비교
"""

from typing import Any, Dict, Optional
import pandas as pd


# 종업원구분 코드 매핑
EMPLOYEE_TYPE_CODES = {
    # 임원
    "임원": "임원",
    "3": "임원",
    "3.0": "임원",
    # 직원 (1, 2 모두 직원으로 처리)
    "직원": "직원",
    "일반직원": "직원",
    "1": "직원",
    "1.0": "직원",
    "2": "직원",
    "2.0": "직원",
    # 계약직
    "계약직": "계약직",
    "4": "계약직",
    "4.0": "계약직",
}


def calculate_aggregates(df: pd.DataFrame) -> Dict[str, Any]:
    """
    DataFrame에서 집계값 계산

    Args:
        df: 파싱된 명부 데이터

    Returns:
        집계 결과 딕셔너리 (Layer 2 검증에서 사용)
    """
    result = {
        "headcount": {},
        "amount": {},
        "summary": {},
    }

    # 1. 종업원구분별 인원수 계산
    emp_type_col = _find_column(df, ["종업원구분", "종업원 구분", "직종구분"])
    if emp_type_col:
        counts = _count_by_employee_type(df, emp_type_col)
        result["headcount"] = {
            "임원인원": int(counts.get("임원", 0)),
            "일반직원인원": int(counts.get("직원", 0)),
            "계약직인원": int(counts.get("계약직", 0)),
            "전체인원": int(len(df)),
        }
    else:
        result["headcount"] = {
            "임원인원": None,
            "일반직원인원": None,
            "계약직인원": None,
            "전체인원": int(len(df)),
        }

    # 2. 금액 합계 계산
    # 당년도 퇴직금추계액
    current_year_col = _find_column(df, ["당년도퇴직금추계액", "당년도 퇴직금추계액", "퇴직금추계액"])
    if current_year_col:
        result["amount"]["당년도퇴직금합계"] = _sum_column(df, current_year_col)

    # 차년도 퇴직금추계액
    next_year_col = _find_column(df, ["차년도퇴직금추계액", "차년도 퇴직금추계액"])
    if next_year_col:
        result["amount"]["차년도퇴직금합계"] = _sum_column(df, next_year_col)

    # 중간정산액
    interim_col = _find_column(df, ["중간정산액", "정산액", "중간정산금액"])
    if interim_col:
        result["amount"]["중간정산합계"] = _sum_column(df, interim_col)

    # 기준급여 합계
    salary_col = _find_column(df, ["기준급여", "급여"])
    if salary_col:
        result["amount"]["기준급여합계"] = _sum_column(df, salary_col)

    # 3. 요약 정보
    result["summary"] = {
        "total_rows": int(len(df)),
        "columns_found": list(df.columns),
    }

    return result


def _find_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """후보 중 DataFrame에 있는 컬럼명 찾기"""
    for col in candidates:
        if col in df.columns:
            return col
        # 부분 매칭 시도
        for df_col in df.columns:
            if col in df_col or df_col in col:
                return df_col
    return None


def _count_by_employee_type(df: pd.DataFrame, col: str) -> Dict[str, int]:
    """종업원구분별 인원수 카운트"""
    counts = {"임원": 0, "직원": 0, "계약직": 0, "기타": 0}

    for val in df[col]:
        val_str = str(val).strip()
        emp_type = EMPLOYEE_TYPE_CODES.get(val_str, "기타")
        counts[emp_type] = counts.get(emp_type, 0) + 1

    return counts


def _sum_column(df: pd.DataFrame, col: str) -> float:
    """컬럼 합계 계산 (숫자가 아닌 값은 무시)"""
    try:
        result = pd.to_numeric(df[col], errors='coerce').sum()
        # numpy.float64 → Python float 변환 (JSON 직렬화 호환)
        return float(result) if pd.notna(result) else 0.0
    except Exception:
        return 0.0


def get_aggregate_for_question(aggregates: Dict[str, Any], question_id: str) -> Optional[float]:
    """
    질문 ID에 해당하는 집계값 반환

    Args:
        aggregates: calculate_aggregates() 결과
        question_id: 진단 질문 ID (q21, q22, ...)

    Returns:
        해당 집계값 또는 None
    """
    mapping = {
        # 인원 집계
        "q21": ("headcount", "임원인원"),
        "q22": ("headcount", "일반직원인원"),
        "q23": ("headcount", "계약직인원"),
        # 금액 집계
        "q27": ("amount", "당년도퇴직금합계"),
        "q28": ("amount", "중간정산합계"),
    }

    if question_id not in mapping:
        return None

    category, key = mapping[question_id]
    return aggregates.get(category, {}).get(key)


def get_aggregates_by_question_id(df: pd.DataFrame) -> Dict[str, float]:
    """
    DataFrame에서 집계값을 계산하여 질문 ID로 매핑된 딕셔너리 반환

    Layer 2 검증에서 직접 사용하는 형태:
    {"q21": 10, "q22": 50, "q23": 5, "q27": 1000000, ...}
    """
    aggregates = calculate_aggregates(df)

    result = {}

    # 인원 집계 (int 보장)
    headcount = aggregates.get("headcount", {})
    if headcount.get("임원인원") is not None:
        result["q21"] = int(headcount["임원인원"])
    if headcount.get("일반직원인원") is not None:
        result["q22"] = int(headcount["일반직원인원"])
    if headcount.get("계약직인원") is not None:
        result["q23"] = int(headcount["계약직인원"])

    # 금액 집계 (float 보장)
    amount = aggregates.get("amount", {})
    if amount.get("당년도퇴직금합계") is not None:
        result["q27"] = float(amount["당년도퇴직금합계"])
    if amount.get("중간정산합계") is not None:
        result["q28"] = float(amount["중간정산합계"])

    return result
