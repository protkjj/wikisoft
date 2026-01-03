"""
Layer 1 검증 (코드 룰 기반) - v2에서 이식
"""
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from core.parsers.standard_schema import get_all_aliases
from core.utils.date_utils import is_valid_yyyymmdd, normalize_date


def validate_layer1(df: pd.DataFrame, diagnostic_answers: Dict[str, str]) -> Dict[str, Any]:
    """Layer 1: 규칙/스키마 기반 유효성 검사."""
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    
    def mask_emp_id(emp_id: Any) -> str:
        """사원번호 (마스킹 비활성화)"""
        return str(emp_id).strip()
    
    def get_emp_info(row, idx) -> str:
        """사원번호 정보 문자열 생성"""
        emp_id = row.get("사원번호", "")
        if emp_id and not pd.isna(emp_id):
            return f"사원번호 {mask_emp_id(emp_id)}"
        return f"행 {idx+2}"

    # 필수 필드 존재 확인 (경고만, 행별 검사는 계속 진행)
    base_required = ["생년월일", "사원번호", "기준급여"]  # 핵심 필드만
    optional_fields = ["이름", "제도구분"]  # 선택적
    
    for col in base_required:
        if col not in df.columns:
            warnings.append({"column": col, "warning": f"권장 필드 없음: {col}", "severity": "warning"})

    has_hire_date = ("입사일" in df.columns) or ("입사일자" in df.columns)
    if not has_hire_date:
        warnings.append({"column": "입사일|입사일자", "warning": "권장 필드 없음: 입사일", "severity": "warning"})

    # 행별 검사 (항상 실행)
    for idx, row in df.iterrows():
        emp_info = get_emp_info(row, idx)
        
        # 필수 값 누락 (존재하는 컬럼만 검사)
        for req_col in ["사원번호", "생년월일", "기준급여"]:
            if req_col in df.columns:
                val = row.get(req_col)
                if pd.isna(val) or str(val).strip() == "":
                    errors.append({"row": idx, "emp_info": emp_info, "column": req_col, "error": "필수 값 누락", "severity": "error"})

        # 전화번호 형식
        phone_aliases = get_all_aliases("전화번호")
        for col in df.columns:
            if col in phone_aliases:
                phone = str(row[col]).strip()
                if phone and not phone.startswith("PHONE_"):
                    digits = re.sub(r"\D", "", phone)
                    if not (digits.startswith("0") and len(digits) in (10, 11)):
                        errors.append({"row": idx, "emp_info": emp_info, "column": col, "error": "전화번호 형식 오류", "severity": "error"})

        # 이메일 형식
        email_aliases = get_all_aliases("이메일")
        for col in df.columns:
            if col in email_aliases:
                email = str(row[col]).strip()
                if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                    warnings.append({"row": idx, "emp_info": emp_info, "column": col, "warning": "이메일 형식 경고", "severity": "warning"})

        # 생년월일: yyyymmdd + 1945~2010
        if "생년월일" in df.columns:
            birth_raw = row["생년월일"]
            birth_norm = normalize_date(birth_raw)
            if not birth_norm or not is_valid_yyyymmdd(birth_norm):
                errors.append({"row": idx, "emp_info": emp_info, "column": "생년월일", "error": "생년월일 형식 오류", "severity": "error"})
            else:
                birth_year = int(birth_norm[:4])
                if birth_year < 1945 or birth_year > 2010:
                    errors.append({"row": idx, "emp_info": emp_info, "column": "생년월일", "error": "생년월일 범위 오류", "severity": "error"})

        # 급여: 양수 + 최저임금 체크
        # 2024년 최저임금: 시급 9,860원 × 209시간 = 월 2,060,740원
        MIN_WAGE_MONTHLY = 2060740
        for sal_col in ["급여", "기준급여"]:
            if sal_col in df.columns:
                try:
                    sal = float(row[sal_col]) if not pd.isna(row[sal_col]) else 0
                    if sal <= 0:
                        errors.append({"row": idx, "emp_info": emp_info, "column": sal_col, "error": f"{sal_col} 음수 또는 0", "severity": "error"})
                    elif sal < MIN_WAGE_MONTHLY:
                        warnings.append({"row": idx, "emp_info": emp_info, "column": sal_col, "warning": f"{sal_col} {sal:,.0f}원 - 최저임금(월 206만원) 미달", "severity": "warning"})
                except (ValueError, TypeError):
                    errors.append({"row": idx, "emp_info": emp_info, "column": sal_col, "error": f"{sal_col} 형식 오류", "severity": "error"})

        # 입사일 > 생년월일 (18세) + 미래 날짜 검사
        hire_col = "입사일" if "입사일" in df.columns else ("입사일자" if "입사일자" in df.columns else None)
        if hire_col and hire_col in df.columns:
            try:
                hire_raw = row[hire_col]
                hire_norm = normalize_date(hire_raw)
                if hire_norm:
                    hire_date = pd.to_datetime(hire_norm, format="%Y%m%d", errors="coerce")
                    if pd.notnull(hire_date):
                        # 미래 입사일 검사
                        if hire_date > pd.Timestamp.now():
                            errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": "입사일이 미래임", "severity": "error"})
                        
                        # 18세 미만 입사 검사
                        if "생년월일" in df.columns:
                            birth_norm = normalize_date(row["생년월일"])
                            if birth_norm:
                                birth_date = pd.to_datetime(birth_norm, format="%Y%m%d", errors="coerce")
                                if pd.notnull(birth_date):
                                    age_at_hire = (hire_date - birth_date).days / 365.25
                                    if age_at_hire < 18:
                                        errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": "입사 나이 18세 미만", "severity": "error"})
                                    
                                    # 고령 입사 경고 (70세 이상)
                                    if age_at_hire > 70:
                                        warnings.append({"row": idx, "emp_info": emp_info, "column": hire_col, "warning": f"입사 나이 {int(age_at_hire)}세 (70세 초과)", "severity": "warning"})
                                    
                                    # 입사일 < 생년월일 (불가능)
                                    if hire_date < birth_date:
                                        errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": "입사일이 생년월일보다 앞섬", "severity": "error"})
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
                        errors.append({"row": idx, "emp_info": emp_info, "column": retire_col, "error": "퇴직일 < 입사일", "severity": "error"})
            except Exception:
                pass

        # 금액 음수 금지
        for amt_col in ["퇴직금", "전환금"]:
            if amt_col in df.columns:
                try:
                    amt = float(row[amt_col]) if not pd.isna(row[amt_col]) else 0
                    if amt < 0:
                        errors.append({"row": idx, "emp_info": emp_info, "column": amt_col, "error": f"{amt_col} 음수", "severity": "error"})
                except (ValueError, TypeError):
                    errors.append({"row": idx, "emp_info": emp_info, "column": amt_col, "error": f"{amt_col} 형식 오류", "severity": "error"})

        # 도메인 값: 성별(1/2)
        gender_col = None
        for c in df.columns:
            if "성별" in c:
                gender_col = c
                break
        if gender_col:
            gender_val = str(row[gender_col]).strip()
            if gender_val and gender_val not in ["1", "2", "1.0", "2.0", "남", "여", "M", "F", "nan"]:
                errors.append({"row": idx, "emp_info": emp_info, "column": gender_col, "error": f"성별 값 오류: {gender_val}", "severity": "error"})

    # 중복 검사 (최적화: O(n²) → O(n))
    if "사원번호" in df.columns:
        # duplicated()로 중복 행만 필터링 (O(n))
        dup_mask = df.duplicated('사원번호', keep=False)
        if dup_mask.any():
            dup_df = df[dup_mask]
            # 이미 필터링된 데이터를 그룹화 (O(n))
            for emp_id, group in dup_df.groupby('사원번호'):
                rows = group.index.tolist()
                emp_id_str = str(emp_id).strip()
                warnings.append({
                    "row": rows[0],
                    "emp_info": f"{emp_id_str} (행 {rows[0]+1})",
                    "column": "사원번호",
                    "warning": f"중복 사원번호 {len(rows)}건",
                    "severity": "warning"
                })

    return {"errors": errors, "warnings": warnings}
