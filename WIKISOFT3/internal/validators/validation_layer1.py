"""
Layer 1 검증 (코드 룰 기반) - v2에서 이식
"""
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from internal.parsers.standard_schema import get_all_aliases
from internal.utils.date_utils import is_valid_yyyymmdd, normalize_date


def validate_layer1(df: pd.DataFrame, diagnostic_answers: Dict[str, str]) -> Dict[str, Any]:
    """Layer 1: 규칙/스키마 기반 유효성 검사."""
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # 필수 필드 존재 확인
    base_required = ["이름", "생년월일", "사원번호", "기준급여", "제도구분"]
    for col in base_required:
        if col not in df.columns:
            errors.append({"column": col, "error": f"필수 필드 누락: {col}", "severity": "error"})

    if ("입사일" not in df.columns) and ("입사일자" not in df.columns):
        errors.append({"column": "입사일|입사일자", "error": "필수 필드 누락: 입사일 또는 입사일자", "severity": "error"})

    if errors:
        return {"errors": errors, "warnings": warnings}

    # 행별 검사
    for idx, row in df.iterrows():
        # 필수 값 누락
        for req_col in ["사원번호", "생년월일", "입사일", "입사일자", "기준급여", "제도구분"]:
            if req_col in df.columns:
                val = row.get(req_col)
                if pd.isna(val) or str(val).strip() == "":
                    errors.append({"row": idx, "column": req_col, "error": "필수 값 누락", "severity": "error"})

        # 전화번호 형식
        phone_aliases = get_all_aliases("전화번호")
        for col in df.columns:
            if col in phone_aliases:
                phone = str(row[col]).strip()
                if phone and not phone.startswith("PHONE_"):
                    digits = re.sub(r"\D", "", phone)
                    if not (digits.startswith("0") and len(digits) in (10, 11)):
                        errors.append({"row": idx, "column": col, "error": "전화번호 형식 오류", "severity": "error"})

        # 이메일 형식
        email_aliases = get_all_aliases("이메일")
        for col in df.columns:
            if col in email_aliases:
                email = str(row[col]).strip()
                if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                    warnings.append({"row": idx, "column": col, "warning": "이메일 형식 경고", "severity": "warning"})

        # 생년월일: yyyymmdd + 1945~2010
        if "생년월일" in df.columns:
            birth_raw = row["생년월일"]
            birth_norm = normalize_date(birth_raw)
            if not birth_norm or not is_valid_yyyymmdd(birth_norm):
                errors.append({"row": idx, "column": "생년월일", "error": "생년월일 형식 오류", "severity": "error"})
            else:
                birth_year = int(birth_norm[:4])
                if birth_year < 1945 or birth_year > 2010:
                    errors.append({"row": idx, "column": "생년월일", "error": "생년월일 범위 오류", "severity": "error"})

        # 급여: 양수
        for sal_col in ["급여", "기준급여"]:
            if sal_col in df.columns:
                try:
                    sal = float(row[sal_col]) if not pd.isna(row[sal_col]) else 0
                    if sal <= 0:
                        errors.append({"row": idx, "column": sal_col, "error": f"{sal_col} 음수 또는 0", "severity": "error"})
                except (ValueError, TypeError):
                    errors.append({"row": idx, "column": sal_col, "error": f"{sal_col} 형식 오류", "severity": "error"})

        # 입사일 > 생년월일 (18세)
        if "생년월일" in df.columns:
            try:
                birth_norm = normalize_date(row["생년월일"])
                hire_col = "입사일" if "입사일" in df.columns else "입사일자"
                hire_norm = normalize_date(row[hire_col])
                if birth_norm and hire_norm:
                    birth_date = pd.to_datetime(birth_norm, format="%Y%m%d", errors="coerce")
                    hire_date = pd.to_datetime(hire_norm, format="%Y%m%d", errors="coerce")
                    if pd.notnull(birth_date) and pd.notnull(hire_date):
                        age_at_hire = (hire_date - birth_date).days / 365.25
                        if age_at_hire < 18:
                            errors.append({"row": idx, "column": hire_col, "error": "입사 나이 18세 미만", "severity": "error"})
            except Exception:
                pass

        # 퇴직일 > 입사일
        retire_col = None
        for c in ["퇴직일", "전환일"]:
            if c in df.columns:
                retire_col = c
                break
        if retire_col:
            try:
                retire_norm = normalize_date(row[retire_col])
                hire_col = "입사일" if "입사일" in df.columns else "입사일자"
                hire_norm = normalize_date(row[hire_col])
                if retire_norm and hire_norm:
                    retire_date = pd.to_datetime(retire_norm, format="%Y%m%d", errors="coerce")
                    hire_date = pd.to_datetime(hire_norm, format="%Y%m%d", errors="coerce")
                    if pd.notnull(retire_date) and pd.notnull(hire_date) and retire_date < hire_date:
                        errors.append({"row": idx, "column": retire_col, "error": "퇴직일 < 입사일", "severity": "error"})
            except Exception:
                pass

        # 금액 음수 금지
        for amt_col in ["퇴직금", "전환금"]:
            if amt_col in df.columns:
                try:
                    amt = float(row[amt_col]) if not pd.isna(row[amt_col]) else 0
                    if amt < 0:
                        errors.append({"row": idx, "column": amt_col, "error": f"{amt_col} 음수", "severity": "error"})
                except (ValueError, TypeError):
                    errors.append({"row": idx, "column": amt_col, "error": f"{amt_col} 형식 오류", "severity": "error"})

        # 도메인 값: 성별(1/2), 제도구분(1/2/3)
        if "성별" in df.columns and str(row["성별"]) not in ["1", "2"]:
            errors.append({"row": idx, "column": "성별", "error": "성별 값 오류", "severity": "error"})
        if "제도구분" in df.columns and str(row["제도구분"]) not in ["1", "2", "3"]:
            errors.append({"row": idx, "column": "제도구분", "error": "제도구분 값 오류", "severity": "error"})

    # 중복 검사
    if "사원번호" in df.columns:
        dup_emp = df.groupby("사원번호").size()
        for emp_id, cnt in dup_emp[dup_emp > 1].items():
            rows = df[df["사원번호"] == emp_id].index.tolist()
            warnings.append({"row": rows[0], "column": "사원번호", "warning": f"중복 사원번호 (행: {rows})", "severity": "warning"})

    return {"errors": errors, "warnings": warnings}
