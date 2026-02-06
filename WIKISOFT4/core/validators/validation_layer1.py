"""
Layer 1 검증 (코드 룰 기반) - v2에서 이식
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from core.parsers.standard_schema import get_all_aliases
from core.utils.date_utils import is_valid_yyyymmdd, normalize_date


def validate_layer1(df: pd.DataFrame, diagnostic_answers: Dict[str, str], mode: str = "full", matches: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Layer 1: 규칙/스키마 기반 유효성 검사.

    Args:
        df: 검증할 DataFrame
        diagnostic_answers: 진단 질문 답변
        mode: 검증 모드 ("roster" = 명부만, "full" = 전체)
              roster 모드에서는 금액 관련 필드 검증 제외
        matches: AI 헤더 매칭 결과 (source → target 매핑)
    """
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # AI 매칭 결과를 표준필드명 → 실제컬럼명 맵으로 변환
    # 예: {"종업원구분": "직종코드", "사원번호": "사번"}
    ai_field_map: Dict[str, str] = {}
    if matches:
        for m in matches:
            if m.get("target") and m.get("source"):
                ai_field_map[m["target"]] = m["source"]

    def mask_emp_id(emp_id: Any) -> str:
        """사원번호 (마스킹 비활성화)"""
        return str(emp_id).strip()

    def get_emp_info(row, idx) -> str:
        """사원번호 정보 문자열 생성"""
        emp_id = row.get("사원번호", "")
        if emp_id and not pd.isna(emp_id):
            return f"사원번호 {mask_emp_id(emp_id)}"
        return f"행 {idx+2}"

    # 필수 필드 (전체 모드: 7개, 명부만 모드: 금액 제외 5개)
    # 차년도퇴직금추계액은 조건부 필수 (임원/계약직만) → 별도 처리
    REQUIRED_FIELDS_FULL = [
        ("사원번호", ["사원번호", "사번"]),
        ("생년월일", ["생년월일"]),
        ("성별", ["성별"]),
        ("입사일자", ["입사일자", "입사일"]),
        ("기준급여", ["기준급여", "급여"]),
        ("당년도퇴직금추계액", ["당년도퇴직금추계액", "당년도 퇴직금추계액", "퇴직금추계액"]),
        ("종업원구분", ["종업원구분", "종업원 구분", "직종구분", "직종 구분", "직원구분", "구분"]),
    ]

    # 조건부 필수: 임원(3)/계약직(4)/정년초과자만 필수
    CONDITIONAL_REQUIRED_FIELDS = [
        ("차년도퇴직금추계액", ["차년도퇴직금추계액", "차년도 퇴직금추계액"]),
    ]

    # 명부만 모드: 금액 관련 필드 제외
    REQUIRED_FIELDS_ROSTER = [
        ("사원번호", ["사원번호", "사번"]),
        ("생년월일", ["생년월일"]),
        ("성별", ["성별"]),
        ("입사일자", ["입사일자", "입사일"]),
        ("종업원구분", ["종업원구분", "종업원 구분", "직종구분", "직종 구분", "직원구분", "구분"]),
    ]

    REQUIRED_FIELDS = REQUIRED_FIELDS_ROSTER if mode == "roster" else REQUIRED_FIELDS_FULL

    # 선택적 필드 (값이 없어도 됨)
    OPTIONAL_FIELDS = [
        ("중간정산기준일", ["중간정산기준일", "중간정산 기준일"]),
        ("중간정산액", ["중간정산액", "중간정산금액"]),
        ("제도구분", ["제도구분", "제도 구분"]),
        ("적용배수", ["적용배수", "배수"]),
    ]

    # 필드명 → 실제 컬럼명 매핑
    def find_column(field_name: str, field_aliases: list) -> Optional[str]:
        # 1. AI 매칭 결과 우선 사용
        if field_name in ai_field_map:
            mapped_col = ai_field_map[field_name]
            if mapped_col in df.columns:
                return mapped_col

        # 2. 별칭(alias)으로 직접 찾기 (fallback)
        for alias in field_aliases:
            if alias in df.columns:
                return alias
        return None

    required_col_map = {}  # {"사원번호": "사번", ...} 실제 컬럼명 매핑
    for field_name, aliases in REQUIRED_FIELDS:
        found_col = find_column(field_name, aliases)
        if found_col:
            required_col_map[field_name] = found_col
        else:
            warnings.append({"column": field_name, "warning": f"필수 필드 없음: {field_name}", "severity": "warning"})

    # 선택적 필드도 매핑 (검증용, 경고 없음)
    optional_col_map = {}
    for field_name, aliases in OPTIONAL_FIELDS:
        found_col = find_column(field_name, aliases)
        if found_col:
            optional_col_map[field_name] = found_col

    # 조건부 필수 필드 매핑 (전체 모드에서만)
    conditional_col_map = {}
    if mode == "full":
        for field_name, aliases in CONDITIONAL_REQUIRED_FIELDS:
            found_col = find_column(field_name, aliases)
            if found_col:
                conditional_col_map[field_name] = found_col

    # 시산일 (작성기준일) 파싱 — 시산일<=입사일, 시산일<=중간정산일 체크에 사용
    eval_date = None
    eval_date_str = diagnostic_answers.get("2-0") if diagnostic_answers else None
    if eval_date_str:
        eval_norm = normalize_date(str(eval_date_str))
        if eval_norm and is_valid_yyyymmdd(eval_norm):
            eval_date = pd.to_datetime(eval_norm, format="%Y%m%d", errors="coerce")

    # 행별 검사 (항상 실행)
    for idx, row in df.iterrows():
        emp_info = get_emp_info(row, idx)

        # 필수 값 누락 (필수 필드만 검사)
        for field_name, actual_col in required_col_map.items():
            val = row.get(actual_col)
            if pd.isna(val) or str(val).strip() == "":
                errors.append({"row": idx, "emp_info": emp_info, "column": actual_col, "error": f"{field_name} 필수 값 누락", "severity": "error"})

        # 조건부 필수 값 검사 (차년도퇴직금추계액: 임원/계약직/정년초과자만)
        if mode == "full" and conditional_col_map:
            emp_type_actual_col = required_col_map.get("종업원구분")
            emp_type_val = ""
            if emp_type_actual_col:
                raw = row.get(emp_type_actual_col, "")
                emp_type_val = str(raw).strip() if not pd.isna(raw) else ""

            # 종업원구분 3(임원), 4(계약직)이면 차년도퇴직금추계액 필수
            requires_next_year = emp_type_val in ["3", "3.0", "4", "4.0", "임원", "계약직"]

            # 정년초과자 체크: 만 60세 이상
            if not requires_next_year:
                birth_col = required_col_map.get("생년월일", "생년월일")
                if birth_col in df.columns:
                    birth_raw = row.get(birth_col)
                    birth_norm = normalize_date(birth_raw)
                    if birth_norm and is_valid_yyyymmdd(birth_norm):
                        birth_year = int(birth_norm[:4])
                        current_year = datetime.now().year
                        if current_year - birth_year >= 60:
                            requires_next_year = True

            if requires_next_year:
                for field_name, actual_col in conditional_col_map.items():
                    val = row.get(actual_col)
                    if pd.isna(val) or str(val).strip() == "":
                        errors.append({"row": idx, "emp_info": emp_info, "column": actual_col, "error": f"{field_name} 필수 값 누락 (임원/계약직/정년초과자)", "severity": "error"})

                # 직종>2: 당년도퇴직금추계액 blank/0 체크
                cur_year_col = required_col_map.get("당년도퇴직금추계액")
                if cur_year_col:
                    cur_val = row.get(cur_year_col)
                    try:
                        cur_num = float(cur_val) if not pd.isna(cur_val) else 0
                    except (ValueError, TypeError):
                        cur_num = 0
                    if pd.isna(cur_val) or str(cur_val).strip() == "" or cur_num == 0:
                        errors.append({"row": idx, "emp_info": emp_info, "column": cur_year_col, "error": "당년도퇴직금추계액 필수 값 누락/0 (임원/계약직/정년초과자)", "severity": "error"})

                    # 직종>2: 당년도퇴직금 < 차년도퇴직금 체크
                    next_year_col = conditional_col_map.get("차년도퇴직금추계액")
                    if next_year_col and cur_num > 0:
                        next_val = row.get(next_year_col)
                        try:
                            next_num = float(next_val) if not pd.isna(next_val) else 0
                        except (ValueError, TypeError):
                            next_num = 0
                        if next_num > 0 and cur_num < next_num:
                            warnings.append({"row": idx, "emp_info": emp_info, "column": cur_year_col, "warning": f"당년도퇴직금추계액({cur_num:,.0f}) < 차년도퇴직금추계액({next_num:,.0f})", "severity": "warning"})

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

        # 급여: 양수 + 최저임금 체크 (전체 모드에서만)
        # 2024년 최저임금: 시급 9,860원 × 209시간 = 월 2,060,740원
        if mode == "full":
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

        # 입사일 검증: 날짜 유효성 + 연령 + 시산일
        hire_col = "입사일" if "입사일" in df.columns else ("입사일자" if "입사일자" in df.columns else None)
        if hire_col and hire_col in df.columns:
            try:
                hire_raw = row[hire_col]
                hire_norm = normalize_date(hire_raw)

                # 입사일 날짜 유효성 (월>12, 일>31, 파싱 불가)
                has_hire_value = hire_raw is not None and not pd.isna(hire_raw) and str(hire_raw).strip() != ""
                if has_hire_value and (not hire_norm or not is_valid_yyyymmdd(hire_norm)):
                    errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": "입사일 날짜 형식 오류 (월>12 or 일>31)", "severity": "error"})

                if hire_norm and is_valid_yyyymmdd(hire_norm):
                    hire_date = pd.to_datetime(hire_norm, format="%Y%m%d", errors="coerce")
                    if pd.notnull(hire_date):
                        # 미래 입사일 검사
                        if hire_date > pd.Timestamp.now():
                            errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": "입사일이 미래임", "severity": "error"})

                        # 시산일 <= 입사일 (평가일 이후 입사자는 명부에 없어야 함)
                        if eval_date and pd.notnull(eval_date) and eval_date <= hire_date:
                            errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": f"시산일({eval_date.strftime('%Y-%m-%d')}) 이전 또는 동일 입사 — 명부 포함 불가", "severity": "error"})

                        # 17세 미만 입사 검사
                        if "생년월일" in df.columns:
                            birth_norm = normalize_date(row["생년월일"])
                            if birth_norm:
                                birth_date = pd.to_datetime(birth_norm, format="%Y%m%d", errors="coerce")
                                if pd.notnull(birth_date):
                                    age_at_hire = (hire_date - birth_date).days / 365.25
                                    if age_at_hire < 17:
                                        errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": f"입사 나이 {int(age_at_hire)}세 (17세 미만)", "severity": "error"})

                                    # 고령 입사 경고 (70세 초과)
                                    if age_at_hire > 70:
                                        errors.append({"row": idx, "emp_info": emp_info, "column": hire_col, "error": f"입사 나이 {int(age_at_hire)}세 (70세 초과)", "severity": "error"})

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

        # 중간정산 논리 검증
        interim_date_col = None
        for c in df.columns:
            if "중간정산" in c and ("기준일" in c or "일자" in c or "날짜" in c):
                interim_date_col = c
                break
        if not interim_date_col and "중간정산기준일" in df.columns:
            interim_date_col = "중간정산기준일"

        interim_amt_col = None
        for c in df.columns:
            if "중간정산" in c and ("액" in c or "금" in c):
                interim_amt_col = c
                break
        if not interim_amt_col and "중간정산액" in df.columns:
            interim_amt_col = "중간정산액"

        # 중간정산기준일 검증
        if interim_date_col:
            try:
                interim_date_raw = row[interim_date_col]
                interim_date_norm = normalize_date(interim_date_raw)

                # 중간정산일 날짜 유효성 (월>12, 일>31, 파싱 불가)
                has_interim_value = interim_date_raw is not None and not pd.isna(interim_date_raw) and str(interim_date_raw).strip() != ""
                if has_interim_value and (not interim_date_norm or not is_valid_yyyymmdd(interim_date_norm)):
                    errors.append({"row": idx, "emp_info": emp_info, "column": interim_date_col, "error": "중간정산일 날짜 형식 오류 (월>12 or 일>31)", "severity": "error"})

                if interim_date_norm and is_valid_yyyymmdd(interim_date_norm):
                    interim_date = pd.to_datetime(interim_date_norm, format="%Y%m%d", errors="coerce")
                    if pd.notnull(interim_date):
                        # 중간정산일 <= 입사일 (7일 이내 허용)
                        hire_col_tmp = "입사일" if "입사일" in df.columns else ("입사일자" if "입사일자" in df.columns else None)
                        if hire_col_tmp:
                            hire_norm_tmp = normalize_date(row[hire_col_tmp])
                            if hire_norm_tmp:
                                hire_date_tmp = pd.to_datetime(hire_norm_tmp, format="%Y%m%d", errors="coerce")
                                if pd.notnull(hire_date_tmp) and interim_date < hire_date_tmp:
                                    days_diff = (hire_date_tmp - interim_date).days
                                    if days_diff > 7:
                                        errors.append({"row": idx, "emp_info": emp_info, "column": interim_date_col, "error": f"중간정산기준일이 입사일보다 {days_diff}일 앞섬", "severity": "error"})

                        # 시산일 <= 중간정산일 (평가일 이전에 중간정산 있어야 함)
                        if eval_date and pd.notnull(eval_date) and eval_date <= interim_date:
                            errors.append({"row": idx, "emp_info": emp_info, "column": interim_date_col, "error": f"중간정산일이 시산일({eval_date.strftime('%Y-%m-%d')}) 이후 — 불가", "severity": "error"})
            except Exception:
                pass

        # 중간정산액 검증
        if interim_amt_col:
            try:
                interim_amt = float(row[interim_amt_col]) if not pd.isna(row[interim_amt_col]) else 0

                # 중간정산액 < 0
                if interim_amt < 0:
                    errors.append({"row": idx, "emp_info": emp_info, "column": interim_amt_col, "error": f"중간정산액 음수 ({interim_amt:,.0f}원)", "severity": "error"})

                # 중간정산액 > 0인데 기준일 없으면 경고
                if interim_amt > 0:
                    has_interim_date = False
                    if interim_date_col:
                        interim_date_val = row[interim_date_col]
                        if not pd.isna(interim_date_val) and str(interim_date_val).strip():
                            has_interim_date = True
                    if not has_interim_date:
                        warnings.append({"row": idx, "emp_info": emp_info, "column": interim_amt_col, "warning": f"중간정산액 {interim_amt:,.0f}원 있으나 기준일 없음", "severity": "warning"})
            except (ValueError, TypeError):
                pass

        # 금액 음수 금지 (전체 모드에서만)
        if mode == "full":
            # 기본 컬럼 + 매핑된 퇴직금추계액 컬럼
            neg_check_cols = ["퇴직금", "전환금"]
            for std_name in ["당년도퇴직금추계액", "차년도퇴직금추계액"]:
                actual = required_col_map.get(std_name) or conditional_col_map.get(std_name)
                if actual and actual not in neg_check_cols:
                    neg_check_cols.append(actual)

            for amt_col in neg_check_cols:
                if amt_col in df.columns:
                    amt_raw = row[amt_col]
                    # 빈 값은 필수 필드 체크에서 처리 → 여기서는 스킵
                    if pd.isna(amt_raw) or str(amt_raw).strip() == "":
                        continue
                    try:
                        amt = float(amt_raw)
                        if amt < 0:
                            errors.append({"row": idx, "emp_info": emp_info, "column": amt_col, "error": f"{amt_col} 음수 ({amt:,.0f}원)", "severity": "error"})
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
            if gender_val and gender_val not in ["1", "2", "1.0", "2.0", "남", "여", "녀", "남자", "여자", "M", "F", "male", "female", "Male", "Female", "nan"]:
                errors.append({"row": idx, "emp_info": emp_info, "column": gender_col, "error": f"성별 값 오류: {gender_val}", "severity": "error"})

        # 도메인 값: 종업원구분 (1:직원, 2:직원, 3:임원, 4:계약직)
        emp_type_col = None
        for c in df.columns:
            if "종업원" in c or "직종" in c or "고용" in c:
                emp_type_col = c
                break
        if emp_type_col:
            emp_type_val = str(row[emp_type_col]).strip()
            valid_emp_types = [
                "1", "2", "3", "4", "1.0", "2.0", "3.0", "4.0",
                "임원", "직원", "일반직원", "계약직", "정규직", "비정규직",
                "nan", ""
            ]
            if emp_type_val and emp_type_val not in valid_emp_types:
                errors.append({"row": idx, "emp_info": emp_info, "column": emp_type_col, "error": f"종업원구분 값 오류: {emp_type_val}", "severity": "error"})

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
