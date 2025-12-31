"""
중복 탐지 모듈 (Duplicate Detection)

다양한 중복 케이스를 탐지:
1. 완전 중복: 사원번호 동일
2. 유사 중복: 이름+생년월일 동일하지만 사원번호 다름
3. 의심 중복: 전화번호/이메일 동일
4. 관계사 전출입 중복: 동일인이 다른 회사에 존재
"""

import pandas as pd
from typing import Any, Dict, List, Optional
from collections import defaultdict


def detect_duplicates(
    df: pd.DataFrame,
    headers: List[str],
    matches: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    중복 행 탐지
    
    Args:
        df: 파싱된 DataFrame
        headers: 원본 헤더 목록
        matches: 헤더 매칭 결과 [{"source": "사번", "target": "사원번호"}, ...]
    
    Returns:
        {
            "has_duplicates": bool,
            "total_duplicates": int,
            "exact_duplicates": [...],   # 완전 중복 (사원번호 동일)
            "similar_duplicates": [...], # 유사 중복 (이름+생년월일)
            "suspicious_duplicates": [...], # 의심 중복 (연락처)
            "summary": str
        }
    """
    result = {
        "has_duplicates": False,
        "total_duplicates": 0,
        "exact_duplicates": [],
        "similar_duplicates": [],
        "suspicious_duplicates": [],
        "summary": ""
    }
    
    if df is None or df.empty:
        return result
    
    # 매핑된 컬럼명 찾기
    col_map = {}
    for m in matches:
        if m.get("target") and not m.get("unmapped"):
            col_map[m["target"]] = m["source"]
    
    # 1. 완전 중복: 사원번호 동일
    emp_col = col_map.get("사원번호")
    if emp_col and emp_col in df.columns:
        result["exact_duplicates"] = _find_exact_duplicates(df, emp_col)
    
    # 2. 유사 중복: 이름+생년월일 동일 (사원번호 다름)
    name_col = col_map.get("이름")
    birth_col = col_map.get("생년월일")
    if name_col and birth_col and name_col in df.columns and birth_col in df.columns:
        result["similar_duplicates"] = _find_similar_duplicates(
            df, emp_col, name_col, birth_col
        )
    
    # 3. 의심 중복: 전화번호 또는 이메일 동일
    phone_col = col_map.get("전화번호")
    email_col = col_map.get("이메일")
    result["suspicious_duplicates"] = _find_suspicious_duplicates(
        df, emp_col, phone_col, email_col
    )
    
    # 총계
    total = (
        len(result["exact_duplicates"]) + 
        len(result["similar_duplicates"]) + 
        len(result["suspicious_duplicates"])
    )
    result["total_duplicates"] = total
    result["has_duplicates"] = total > 0
    
    # 요약
    parts = []
    if result["exact_duplicates"]:
        parts.append(f"완전중복 {len(result['exact_duplicates'])}건")
    if result["similar_duplicates"]:
        parts.append(f"유사중복 {len(result['similar_duplicates'])}건")
    if result["suspicious_duplicates"]:
        parts.append(f"의심중복 {len(result['suspicious_duplicates'])}건")
    result["summary"] = ", ".join(parts) if parts else "중복 없음"
    
    return result


def _find_exact_duplicates(df: pd.DataFrame, emp_col: str) -> List[Dict[str, Any]]:
    """완전 중복 찾기 (사원번호 동일)"""
    duplicates = []
    
    # 사원번호별 그룹화
    emp_groups = df.groupby(emp_col)
    
    for emp_id, group in emp_groups:
        if len(group) > 1:
            rows = group.index.tolist()
            duplicates.append({
                "type": "exact",
                "severity": "error",
                "key": str(emp_id),
                "key_field": "사원번호",
                "rows": rows,
                "count": len(rows),
                "message": f"사원번호 '{emp_id}' 중복 ({len(rows)}건, 행: {[r+2 for r in rows]})"
            })
    
    return duplicates


def _find_similar_duplicates(
    df: pd.DataFrame, 
    emp_col: Optional[str],
    name_col: str, 
    birth_col: str
) -> List[Dict[str, Any]]:
    """유사 중복 찾기 (이름+생년월일 동일, 사원번호 다름)"""
    duplicates = []
    
    # 이름+생년월일 조합으로 그룹화
    df_copy = df.copy()
    df_copy["_name_birth_key"] = df_copy[name_col].astype(str) + "_" + df_copy[birth_col].astype(str)
    
    name_birth_groups = df_copy.groupby("_name_birth_key")
    
    for key, group in name_birth_groups:
        if len(group) > 1:
            # 사원번호가 모두 같으면 exact duplicate에서 처리됨 → 스킵
            if emp_col and emp_col in df.columns:
                unique_emp_ids = group[emp_col].nunique()
                if unique_emp_ids == 1:
                    continue  # 같은 사원번호 → exact duplicate
            
            rows = group.index.tolist()
            name_val = str(group[name_col].iloc[0])
            birth_val = str(group[birth_col].iloc[0])
            
            # 사원번호 목록
            emp_ids = []
            if emp_col and emp_col in df.columns:
                emp_ids = group[emp_col].tolist()
            
            duplicates.append({
                "type": "similar",
                "severity": "warning",
                "key": f"{name_val}_{birth_val}",
                "key_field": "이름+생년월일",
                "rows": rows,
                "count": len(rows),
                "emp_ids": emp_ids,
                "message": f"'{name_val}' (생년월일: {birth_val}) 유사 중복 - 사원번호 다름 ({len(rows)}건)"
            })
    
    return duplicates


def _find_suspicious_duplicates(
    df: pd.DataFrame,
    emp_col: Optional[str],
    phone_col: Optional[str],
    email_col: Optional[str]
) -> List[Dict[str, Any]]:
    """의심 중복 찾기 (전화번호/이메일 동일)"""
    duplicates = []
    
    def check_field(col: str, field_name: str):
        if col and col in df.columns:
            # 빈 값 제외
            df_filtered = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
            if df_filtered.empty:
                return
            
            groups = df_filtered.groupby(col)
            for val, group in groups:
                if len(group) > 1:
                    rows = group.index.tolist()
                    
                    # 같은 사원번호면 스킵 (가족 등 다른 케이스)
                    if emp_col and emp_col in df.columns:
                        unique_emp_ids = group[emp_col].nunique()
                        if unique_emp_ids == 1:
                            continue
                    
                    emp_ids = []
                    if emp_col and emp_col in df.columns:
                        emp_ids = group[emp_col].tolist()
                    
                    duplicates.append({
                        "type": "suspicious",
                        "severity": "info",
                        "key": str(val),
                        "key_field": field_name,
                        "rows": rows,
                        "count": len(rows),
                        "emp_ids": emp_ids,
                        "message": f"{field_name} '{val}' 중복 사용 ({len(rows)}명)"
                    })
    
    check_field(phone_col, "전화번호")
    check_field(email_col, "이메일")
    
    return duplicates


def get_duplicate_summary_for_report(duplicates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """리포트용 중복 요약 생성"""
    items = []
    
    for dup in duplicates.get("exact_duplicates", []):
        items.append({
            "type": "duplicate",
            "severity": "error",
            "message": dup["message"],
            "rows": dup["rows"],
            "auto_fix": None  # 자동 수정 불가
        })
    
    for dup in duplicates.get("similar_duplicates", []):
        items.append({
            "type": "duplicate",
            "severity": "warning", 
            "message": dup["message"],
            "rows": dup["rows"],
            "auto_fix": "동일인 여부 확인 필요"
        })
    
    for dup in duplicates.get("suspicious_duplicates", []):
        items.append({
            "type": "duplicate",
            "severity": "info",
            "message": dup["message"],
            "rows": dup["rows"],
            "auto_fix": "연락처 확인 권장"
        })
    
    return items
