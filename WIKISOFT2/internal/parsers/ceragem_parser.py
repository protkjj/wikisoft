import io
import re
from typing import Dict, Any, Tuple, List

import pandas as pd
try:
    import xlrd  # for precise cell (xls)
except Exception:
    xlrd = None

from internal.utils.date_utils import normalize_date
from internal.ai.column_matcher import ai_match_columns, apply_mapping_to_dataframe


# I40-I51 Label Mapping (based on actual sheet structure)
CELL_I40_I51_LABELS = {
    'I40': '',  # Empty in actual file
    'I41': '퇴직금 (a)',
    'I42': '중간정산금액 (b)',
    'I43': 'DC 전환금 (c)',
    'I44': '급여지급액 소계 (a+b+c)',
    'I45': '관계사 전입액 (d)',
    'I46': '관계사 전출액 (e)',
    'I47': '관계사전입전출 소계 (d-e)',
    'I48': '사업결합액 (f)',
    'I49': '사업처분액 (g)',
    'I50': '사업결합처분 소계 (f-g)',
    'I51': '퇴직부채 감소(증가)액 합계 (A-B-C)'
}


def _standardize_headers(df: pd.DataFrame, sheet_type: str = "재직자") -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """
    AI 기반 헤더 표준화
    
    Args:
        df: 원본 DataFrame
        sheet_type: "재직자", "퇴직자", "추가"
        
    Returns:
        (표준화된 DataFrame, 경고 리스트)
    """
    import os
    warnings = []
    
    # 1. AI 매칭 실행 (환경변수에서 API 키 가져옴)
    customer_headers = [str(col).strip() for col in df.columns]
    api_key = os.getenv("OPENAI_API_KEY")
    mapping_result = ai_match_columns(customer_headers, sheet_type=sheet_type, api_key=api_key)
    
    # 2. 매핑 적용
    df_standardized = apply_mapping_to_dataframe(df, mapping_result)
    
    # 3. 경고 수집
    if mapping_result.get("warnings"):
        for warning in mapping_result["warnings"]:
            severity = warning.get("severity", "info")
            message = warning.get("message", "")
            
            warnings.append({
                "sheet_type": sheet_type,
                "severity": severity,
                "message": message,
                "details": warning.get("details", {})
            })
            
            # 콘솔 출력
            if severity == "error":
                print(f"❌ [{sheet_type}] {message}")
            elif severity == "warning":
                print(f"⚠️  [{sheet_type}] {message}")
    
    # 4. AI 사용 여부 확인
    if not mapping_result.get("used_ai"):
        warning_msg = f"폴백 매칭 사용됨 - OpenAI API 키 설정 권장"
        warnings.append({
            "sheet_type": sheet_type,
            "severity": "warning",
            "message": warning_msg,
            "details": {"used_ai": False}
        })
        print(f"⚠️  [{sheet_type}] {warning_msg}")
    
    # 5. 매칭 실패 로깅
    if mapping_result.get("unmapped"):
        print(f"⚠️  [{sheet_type}] 매칭 안 된 컬럼: {mapping_result['unmapped']}")
    
    if mapping_result.get("missing_required"):
        print(f"❌ [{sheet_type}] 필수 필드 누락: {mapping_result['missing_required']}")
    
    return df_standardized, warnings


def _to_numeric(series_or_df) -> pd.Series:
    """Series를 숫자로 변환 (안전 처리)"""
    if isinstance(series_or_df, pd.DataFrame):
        # DataFrame이 들어온 경우 첫 번째 컬럼 사용
        series = series_or_df.iloc[:, 0]
    else:
        series = series_or_df
    
    return pd.to_numeric(series.astype(str).str.replace(',', ''), errors='coerce')


def _normalize_dates(df: pd.DataFrame, columns: Tuple[str, ...]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            # 컬럼이 중복되지 않았는지 확인
            col_data = df[col]
            if isinstance(col_data, pd.DataFrame):
                col_data = col_data.iloc[:, 0]
            df[col] = col_data.apply(lambda v: normalize_date(v) or pd.NA)
    return df


def parse_active(df: pd.DataFrame) -> Dict[str, Any]:
    df, _ = _standardize_headers(df, sheet_type="재직자")  # warnings 무시 (이미 print됨)
    
    # 중복 컬럼 제거 (매칭 오류 방지)
    df = df.loc[:, ~df.columns.duplicated()]
    
    df = _normalize_dates(df, ('생년월일', '입사일자'))
    
    # Numeric conversions (안전하게)
    for col in ('기준급여', '당년도퇴직금추계액', '차년도퇴직금추계액'):
        if col in df.columns:
            df[col] = _to_numeric(df[col])
    
    # Summary 안전 계산
    def safe_sum(df, col_name):
        if col_name not in df.columns:
            return 0.0
        col_data = df[col_name]
        if isinstance(col_data, pd.DataFrame):
            col_data = col_data.iloc[:, 0]
        return float(col_data.sum(skipna=True))
    
    summary = {
        'count': int(len(df)),
        'sum_this_year': safe_sum(df, '당년도퇴직금추계액'),
        'sum_next_year': safe_sum(df, '차년도퇴직금추계액'),
    }
    return {'rows': df.to_dict(orient='records'), 'summary': summary}


def parse_retired_dc(df: pd.DataFrame) -> Dict[str, Any]:
    df, _ = _standardize_headers(df, sheet_type="퇴직자")  # warnings 무시 (이미 print됨)
    df = _normalize_dates(df, ('퇴직일',))
    
    # 퇴직금 컬럼 (표준화 후 이름)
    retire_col = '퇴직금' if '퇴직금' in df.columns else None
    if retire_col:
        df[retire_col] = _to_numeric(df[retire_col])
    
    summary = {
        'count': int(len(df)),
        'sum_amount': float(df.get(retire_col, pd.Series(dtype=float)).sum(skipna=True)) if retire_col else 0.0,
    }
    return {'rows': df.to_dict(orient='records'), 'summary': summary}


def parse_additional(df: pd.DataFrame) -> Dict[str, Any]:
    df, _ = _standardize_headers(df, sheet_type="추가")  # warnings 무시 (이미 print됨)
    # Try common numeric columns
    num_cols = [c for c in df.columns if df[c].dtype in (int, float)]
    total = 0.0
    for c in df.columns:
        s = pd.to_numeric(df[c], errors='coerce')
        if s.notnull().any():
            total += float(s.sum(skipna=True))
    summary = {'count': int(len(df)), 'sum_total_numeric': total}
    return {'rows': df.to_dict(orient='records'), 'summary': summary}


def parse_all(file_bytes: bytes) -> Dict[str, Any]:
    excel = io.BytesIO(file_bytes)
    # Load sheets
    active = pd.read_excel(excel, sheet_name='(2-2) 재직자 명부')
    retired = pd.read_excel(io.BytesIO(file_bytes), sheet_name='(2-3) 퇴직자 및 DC전환자 명부')
    additional = pd.read_excel(io.BytesIO(file_bytes), sheet_name='(2-4) 추가 명부')
    # Core info (1-2) 지정 셀 파싱 (xls 전용)
    core_info = None
    def col_idx(letter: str) -> int:
        # A=0, B=1, ..., I=8
        return ord(letter.upper()) - ord('A')
    def read_col_range(sh, col_letter: str, start_row: int, end_row: int) -> List[Any]:
        values = []
        c = col_idx(col_letter)
        for r in range(start_row-1, end_row):  # 1-based → 0-based
            try:
                cell = sh.cell(r, c)
                values.append(cell.value)
            except Exception:
                values.append(None)
        return values
    def read_cell(sh, col_letter: str, row_num: int):
        try:
            return sh.cell(row_num-1, col_idx(col_letter)).value
        except Exception:
            return None
    try:
        if xlrd:
            wb = xlrd.open_workbook(file_contents=file_bytes)
            # Resolve exact sheet name by searching
            target_name = None
            for name in wb.sheet_names():
                if '(1-2)' in name and '퇴직급여' in name:
                    target_name = name
                    break
            if target_name:
                sh = wb.sheet_by_name(target_name)
                core_info = {
                    'sheet_name': target_name,
                    'company_info_D12_D17': [read_cell(sh, 'D', r) for r in range(12, 18)],
                    'counts_I25_I33': read_col_range(sh, 'I', 25, 33),
                    'counts_I34_I39': read_col_range(sh, 'I', 34, 39),
                    'sums_I40_I51': read_col_range(sh, 'I', 40, 51),
                    'settings_I62_I85': read_col_range(sh, 'I', 62, 85),
                    'discount_D121': read_cell(sh, 'D', 121),
                    'misc_F103_F118': [read_cell(sh, 'F', r) for r in range(103, 119)],
                    'category_F126': read_cell(sh, 'F', 126),
                }
            else:
                core_info = None
        else:
            # Fallback: detect presence via pandas
            core_df = pd.read_excel(io.BytesIO(file_bytes), sheet_name='(1-2) 기초자료_퇴직급여')
            core_info = {'sheet_name': '(1-2) 기초자료_퇴직급여', 'sheet_columns': core_df.columns.tolist(), 'rows': int(len(core_df))}
    except Exception:
        # Final fallback: try to find any sheet containing '(1-2)'
        try:
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            target = None
            for name in xls.sheet_names:
                if '(1-2)' in name:
                    target = name
                    break
            if target:
                df_core = pd.read_excel(io.BytesIO(file_bytes), sheet_name=target)
                core_info = {'sheet_name': target, 'sheet_columns': df_core.columns.tolist(), 'rows': int(len(df_core))}
            else:
                core_info = None
        except Exception:
            core_info = None

    parsed_active = parse_active(active)
    parsed_retired = parse_retired_dc(retired)
    parsed_additional = parse_additional(additional)

    # Cross-checks (basic + core totals if available)
    cross_checks = []
    total_count = parsed_active['summary']['count'] + parsed_retired['summary']['count']
    cross_checks.append({
        'type': 'total_count_active_plus_retired',
        'value': total_count,
        'status': 'computed'
    })
    if core_info:
        cross_checks.append({
            'type': 'core_info_present',
            'status': 'present'
        })
        # If counts are numeric, compare sums
        def safe_sum(lst):
            s = 0
            for v in lst:
                try:
                    s += float(v)
                except Exception:
                    pass
            return s
        counts_25_33 = core_info.get('counts_I25_I33', [])
        # Skip first element (I25) which holds evaluation date like 251231
        counts_sum = safe_sum(counts_25_33[1:]) + safe_sum(core_info.get('counts_I34_I39', []))
        cross_checks.append({
            'type': 'core_counts_sum_I25_I39',
            'value': counts_sum,
            'status': 'computed'
        })
        # Formula checks: ALL formulas in (1-2) sheet
        try:
            c = counts_25_33  # [I25, I26, I27, I28, I29, I30, I31, I32, I33]
            c34_39 = core_info.get('counts_I34_I39', [])  # [I34, I35, I36, I37, I38, I39]
            s = core_info.get('sums_I40_I51', [])  # [I40, I41, ..., I51]
            
            # I26+I27+I28 = I29 (재직자수 합계)
            if len(c) >= 9:
                g1_sum = float(c[1]) + float(c[2]) + float(c[3])
                g1_tot = float(c[4])
                cross_checks.append({
                    'type': 'formula_I26_28_eq_I29',
                    'label': '재직자수 합계 (임원+직원+계약직)',
                    'lhs': g1_sum, 'rhs': g1_tot, 'diff': g1_sum - g1_tot,
                    'status': 'match' if abs(g1_sum - g1_tot) < 1e-6 else 'mismatch'
                })
            
            # I30+I31+I32 = I33 (퇴직자수 합계)
            if len(c) >= 9:
                g2_sum = float(c[5]) + float(c[6]) + float(c[7])
                g2_tot = float(c[8])
                cross_checks.append({
                    'type': 'formula_I30_32_eq_I33',
                    'label': '퇴직자수 합계 (임원+직원+계약직)',
                    'lhs': g2_sum, 'rhs': g2_tot, 'diff': g2_sum - g2_tot,
                    'status': 'match' if abs(g2_sum - g2_tot) < 1e-6 else 'mismatch'
                })
            
            # I36+I37+I38 = I39 (퇴직금 추계액 합계) - indices 2,3,4 → 5 in c34_39
            if len(c34_39) >= 6:
                proj_sum = float(c34_39[2]) + float(c34_39[3]) + float(c34_39[4])
                proj_tot = float(c34_39[5])
                cross_checks.append({
                    'type': 'formula_I36_38_eq_I39',
                    'label': '퇴직금 추계액 합계 (임원+직원+계약직)',
                    'lhs': proj_sum, 'rhs': proj_tot, 'diff': proj_sum - proj_tot,
                    'status': 'match' if abs(proj_sum - proj_tot) < 1e-6 else 'mismatch'
                })
            
            # I41+I42+I43 = I44 (급여지급액 소계)
            if len(s) >= 5:
                pay_sum = float(s[1]) + float(s[2]) + float(s[3])
                pay_tot = float(s[4])
                cross_checks.append({
                    'type': 'formula_I41_43_eq_I44',
                    'label': '급여지급액 소계 (퇴직금+중간정산+DC전환)',
                    'lhs': pay_sum, 'rhs': pay_tot, 'diff': pay_sum - pay_tot,
                    'status': 'match' if abs(pay_sum - pay_tot) < 1e-6 else 'mismatch'
                })
            
            # I45-I46 = I47 (관계사전입전출 소계)
            if len(s) >= 8:
                trans_diff = float(s[5]) - float(s[6])
                trans_tot = float(s[7])
                cross_checks.append({
                    'type': 'formula_I45_minus_I46_eq_I47',
                    'label': '관계사 전입전출 소계 (전입-전출)',
                    'lhs': trans_diff, 'rhs': trans_tot, 'diff': trans_diff - trans_tot,
                    'status': 'match' if abs(trans_diff - trans_tot) < 1e-6 else 'mismatch'
                })
            
            # I48-I49 = I50 (사업결합처분 소계)
            if len(s) >= 11:
                biz_diff = float(s[8]) - float(s[9])
                biz_tot = float(s[10])
                cross_checks.append({
                    'type': 'formula_I48_minus_I49_eq_I50',
                    'label': '사업결합처분 소계 (결합-처분)',
                    'lhs': biz_diff, 'rhs': biz_tot, 'diff': biz_diff - biz_tot,
                    'status': 'match' if abs(biz_diff - biz_tot) < 1e-6 else 'mismatch'
                })
            
            # I44-I47-I50 = I51 (퇴직부채 감소증가액 합계 A-B-C)
            if len(s) >= 12:
                final_calc = float(s[4]) - float(s[7]) - float(s[10])
                final_tot = float(s[11])
                cross_checks.append({
                    'type': 'formula_I44_minus_I47_I50_eq_I51',
                    'label': '퇴직부채 감소증가액 합계 (A-B-C)',
                    'lhs': final_calc, 'rhs': final_tot, 'diff': final_calc - final_tot,
                    'status': 'match' if abs(final_calc - final_tot) < 1e-6 else 'mismatch'
                })
        except Exception as e:
            cross_checks.append({
                'type': 'formula_checks_error',
                'status': 'error',
                'message': str(e)
            })
        sums_total = safe_sum(core_info.get('sums_I40_I51', []))
        cross_checks.append({
            'type': 'core_amounts_sum_I40_I51',
            'value': sums_total,
            'status': 'computed'
        })
        # Compare people counts
        cross_checks.append({
            'type': 'compare_counts_core_vs_lists',
            'core_total': counts_sum,
            'lists_total': total_count,
            'diff': counts_sum - total_count,
            'status': 'match' if abs(counts_sum - total_count) < 1e-6 else 'mismatch'
        })
        # Compare amounts (active-this-year + retired/DC + additional)
        computed_amounts = (
            float(parsed_active['summary'].get('sum_this_year', 0.0)) +
            float(parsed_retired['summary'].get('sum_amount', 0.0)) +
            float(parsed_additional['summary'].get('sum_total_numeric', 0.0))
        )
        cross_checks.append({
            'type': 'compare_amounts_core_vs_lists',
            'core_total': sums_total,
            'lists_total': computed_amounts,
            'diff': computed_amounts - sums_total,
            'status': 'match' if abs(computed_amounts - sums_total) < 1e-2 else 'mismatch'
        })
    else:
        cross_checks.append({
            'type': 'core_info_present',
            'status': 'missing'
        })

    return {
        'active': parsed_active,
        'retired_dc': parsed_retired,
        'additional': parsed_additional,
        'core_info': core_info,
        'cross_checks': cross_checks
    }
