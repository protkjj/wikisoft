import pandas as pd
import re
from datetime import datetime, timedelta
from typing import List, Dict
from internal.utils.date_utils import normalize_date, is_valid_yyyymmdd
from internal.parsers.standard_schema import get_all_aliases, find_field_by_alias


def validate_layer1(df: pd.DataFrame, diagnostic_answers: Dict[str, str]) -> Dict:
    """
    Layer 1 검증 (코드 룰 기반)
    
    Returns:
    {
        "errors": [...],
        "warnings": [...]
    }
    """
    errors = []
    warnings = []
    
    # 필수 필드 검사 (명부 공통 + Ceragem 주요 필드)
    base_required = ['이름', '생년월일', '사원번호', '기준급여', '제도구분']
    for col in base_required:
        if col not in df.columns:
            errors.append({
                'column': col,
                'error': f'필수 필드 누락: {col}',
                'severity': 'error'
            })
    # 입사일/입사일자 중 하나는 반드시 존재
    if ('입사일' not in df.columns) and ('입사일자' not in df.columns):
        errors.append({
            'column': '입사일|입사일자',
            'error': '필수 필드 누락: 입사일 또는 입사일자',
            'severity': 'error'
        })
    
    if errors:  # 필수 필드 없으면 더 이상 검사 불가
        return {'errors': errors, 'warnings': warnings}
    
    # 각 행별 검사
    for idx, row in df.iterrows():
        # 0. 필수 값 누락 검사 (행 단위)
        for req_col in ['사원번호', '생년월일', '입사일', '입사일자', '기준급여', '제도구분']:
            if req_col in df.columns:
                val = row.get(req_col)
                if pd.isna(val) or str(val).strip() == "":
                    errors.append({
                        'row': idx,
                        'column': req_col,
                        'original_value': str(val),
                        'error': '필수 값 누락',
                        'severity': 'error'
                    })
        # 1. 전화번호/이메일: 기본 형식 검사
        # 표준 스키마 사용하여 전화번호 필드 찾기
        phone_value = None
        phone_aliases = get_all_aliases('전화번호')
        for col in df.columns:
            if col in phone_aliases:
                phone_value = row[col]
                break
        if phone_value is not None:
            phone = str(phone_value).strip()
            if not phone.startswith('PHONE_'):  # 마스킹 안 된 경우만 검사
                digits = re.sub(r'\D', '', phone)
                if not (digits.startswith('0') and len(digits) in (10, 11)):
                    errors.append({
                        'row': idx,
                        'column': '전화/휴대폰',
                        'original_value': phone,
                        'error': '전화번호 형식 오류 (0으로 시작, 10~11자리)',
                        'severity': 'error'
                    })
        
        # 이메일 검사 - 표준 스키마 사용
        email_aliases = get_all_aliases('이메일')
        email_col = None
        for col in df.columns:
            if col in email_aliases:
                email_col = col
                break
        if email_col:
            email = str(row[email_col]).strip()
            if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                warnings.append({
                    'row': idx,
                    'column': email_col,
                    'original_value': email,
                    'warning': '이메일 형식 경고 (RFC 기본형식 불일치)',
                    'severity': 'warning'
                })
        
        # 2. 생년월일: yyyymmdd 형식 & 1945~2010 범위
        birth_raw = row['생년월일']
        birth_norm = normalize_date(birth_raw)
        if not birth_norm or not is_valid_yyyymmdd(birth_norm):
            errors.append({
                'row': idx,
                'column': '생년월일',
                'original_value': str(birth_raw),
                'error': '생년월일 형식 오류 (YYYYMMDD)',
                'severity': 'error'
            })
        else:
            birth_year = int(birth_norm[:4])
            if birth_year < 1945 or birth_year > 2010:
                errors.append({
                    'row': idx,
                    'column': '생년월일',
                    'original_value': str(birth_raw),
                    'error': '생년월일 범위 오류 (1945~2010)',
                    'severity': 'error'
                })
        
        # 3. 급여/기준급여: 양수 & 1~100000 범위 (만원 단위)
        # 급여 필드는 선택적이므로 존재 여부 확인
        if '급여' in df.columns:
            try:
                salary = float(row['급여']) if not pd.isna(row['급여']) else 0
                if salary <= 0 or salary > 100000:
                    errors.append({
                        'row': idx,
                        'column': '급여',
                        'original_value': salary,
                        'error': f'급여 범위 오류 (1~100,000 만원)',
                        'severity': 'error'
                    })
            except (ValueError, TypeError):
                errors.append({
                    'row': idx,
                    'column': '급여',
                    'original_value': row['급여'],
                    'error': '급여 형식 오류 (숫자)',
                    'severity': 'error'
                })
        if '기준급여' in df.columns:
            try:
                base_salary = float(row['기준급여']) if not pd.isna(row['기준급여']) else 0
                if base_salary <= 0:
                    errors.append({
                        'row': idx,
                        'column': '기준급여',
                        'original_value': base_salary,
                        'error': '기준급여는 0 초과여야 합니다',
                        'severity': 'error'
                    })
            except (ValueError, TypeError):
                errors.append({
                    'row': idx,
                    'column': '기준급여',
                    'original_value': row.get('기준급여'),
                    'error': '기준급여 형식 오류 (숫자)',
                    'severity': 'error'
                })
        
        # 4. 입사일 > 생년월일 (최소 18세)
        try:
            birth_norm = normalize_date(row['생년월일'])
            hire_value = row['입사일'] if '입사일' in df.columns else row.get('입사일자')
            hire_norm = normalize_date(hire_value)
            if birth_norm and hire_norm:
                birth_date = pd.to_datetime(birth_norm, format='%Y%m%d', errors='coerce')
                hire_date = pd.to_datetime(hire_norm, format='%Y%m%d', errors='coerce')
                if pd.notnull(birth_date) and pd.notnull(hire_date):
                    age_at_hire = (hire_date - birth_date).days / 365.25
                    if age_at_hire < 18:
                        errors.append({
                            'row': idx,
                            'column': '입사일자',
                            'original_value': hire_value,
                            'error': '입사 나이 18세 미만',
                            'severity': 'error'
                        })
                    if hire_date > pd.Timestamp.now():
                        warnings.append({
                            'row': idx,
                            'column': '입사일자',
                            'original_value': hire_value,
                            'warning': '입사일이 미래 날짜입니다',
                            'severity': 'warning'
                        })
        except Exception:
            pass  # 날짜 파싱 실패는 이미 위에서 에러로 처리됨

        # 5. 퇴직/전환일 논리: 퇴직일/전환일 > 입사일자 & 미래일자 경고
        retire_value = row.get('퇴직일') or row.get('전환일')
        if retire_value is not None:
            try:
                retire_norm = normalize_date(retire_value)
                hire_value = row['입사일'] if '입사일' in df.columns else row.get('입사일자')
                hire_norm = normalize_date(hire_value)
                if retire_norm and hire_norm:
                    retire_date = pd.to_datetime(retire_norm, format='%Y%m%d', errors='coerce')
                    hire_date = pd.to_datetime(hire_norm, format='%Y%m%d', errors='coerce')
                    if pd.notnull(retire_date) and pd.notnull(hire_date):
                        if retire_date < hire_date:
                            errors.append({
                                'row': idx,
                                'column': '퇴직/전환일',
                                'original_value': retire_value,
                                'error': '퇴직/전환일이 입사일자보다 이전입니다',
                                'severity': 'error'
                            })
                        if retire_date > pd.Timestamp.now():
                            warnings.append({
                                'row': idx,
                                'column': '퇴직/전환일',
                                'original_value': retire_value,
                                'warning': '퇴직/전환일이 미래 날짜입니다',
                                'severity': 'warning'
                            })
            except Exception:
                errors.append({
                    'row': idx,
                    'column': '퇴직/전환일',
                    'original_value': retire_value,
                    'error': '퇴직/전환일 형식 오류 (YYYYMMDD)',
                    'severity': 'error'
                })

        # 6. 금액 음수 금지: 퇴직금/전환금
        for amt_col in ['퇴직금', '전환금']:
            if amt_col in df.columns:
                try:
                    amt = float(row[amt_col]) if not pd.isna(row[amt_col]) else 0
                    if amt < 0:
                        errors.append({
                            'row': idx,
                            'column': amt_col,
                            'original_value': amt,
                            'error': f'{amt_col} 음수 금지',
                            'severity': 'error'
                        })
                except (ValueError, TypeError):
                    errors.append({
                        'row': idx,
                        'column': amt_col,
                        'original_value': row.get(amt_col),
                        'error': f'{amt_col} 형식 오류 (숫자)',
                        'severity': 'error'
                    })
    
    # 5. 중복 검사 (사원번호, 이름 + 생년월일)
    # 중복 검사는 생년월일을 정규화한 값 기준으로 수행
    df_dup = df.copy()
    if '생년월일' in df_dup.columns:
        df_dup['생년월일'] = df_dup['생년월일'].apply(lambda x: normalize_date(x) or str(x))
    # 사원번호 중복
    if '사원번호' in df_dup.columns:
        emp_dups = df_dup.groupby(['사원번호']).size()
        for emp_id, cnt in emp_dups[emp_dups > 1].items():
            rows = df_dup[df_dup['사원번호'] == emp_id].index.tolist()
            warnings.append({
                'row': rows[0],
                'column': '사원번호',
                'original_value': str(emp_id),
                'warning': f'사원번호 중복 (행: {rows})',
                'severity': 'warning'
            })
    duplicates = df_dup.groupby(['이름', '생년월일']).size()
    duplicate_groups = duplicates[duplicates > 1].index.tolist()
    
    for name, birth in duplicate_groups:
        dup_rows = df_dup[(df_dup['이름'] == name) & (df_dup['생년월일'] == birth)].index.tolist()
        for row_idx in dup_rows:
            warnings.append({
                'row': row_idx,
                'column': 'name_birth',
                'original_value': f'{name} ({birth})',
                'warning': f'중복 직원 발견 (행: {dup_rows})',
                'severity': 'warning'
            })

    # 6. 도메인 범위: 성별, 제도구분 값 검사
    if '성별' in df.columns:
        invalid_gender_rows = df[~df['성별'].astype(str).isin(['1', '2'])].index.tolist()
        for r in invalid_gender_rows:
            errors.append({
                'row': r,
                'column': '성별',
                'original_value': str(df.loc[r, '성별']),
                'error': '성별 값 오류 (1 또는 2)',
                'severity': 'error'
            })
    if '제도구분' in df.columns:
        invalid_scheme_rows = df[~df['제도구분'].astype(str).isin(['1', '2', '3'])].index.tolist()
        for r in invalid_scheme_rows:
            errors.append({
                'row': r,
                'column': '제도구분',
                'original_value': str(df.loc[r, '제도구분']),
                'error': '제도구분 값 오류 (1,2,3)',
                'severity': 'error'
            })
    
    return {
        'errors': errors,
        'warnings': warnings
    }
