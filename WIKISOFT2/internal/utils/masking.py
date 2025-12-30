"""
민감 정보 자동 마스킹 유틸
- 전화번호: 010-****-5678
- 생년월일: 1990-**-**
- 급여: 5000만원 → 50**만원
"""
import re
import pandas as pd
from typing import Any, Dict, List


def mask_phone(phone: str) -> str:
    """
    전화번호 마스킹
    예: 01012345678 → 010-****-5678
    """
    if not isinstance(phone, str):
        return str(phone)
    
    phone = str(phone).strip()
    
    # 이미 마스킹됨
    if "****" in phone:
        return phone
    
    # 숫자만 추출
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11:  # 01X-XXXX-XXXX
        return f"{digits[:3]}-****-{digits[-4:]}"
    elif len(digits) == 10:  # 02-XXXX-XXXX
        return f"{digits[:2]}-****-{digits[-4:]}"
    
    return phone


def mask_birth_date(birth: str) -> str:
    """
    생년월일 마스킹
    예: 1990-05-15 → 1990-**-**
    """
    if not isinstance(birth, str):
        return str(birth)
    
    birth = str(birth).strip()
    
    # 이미 마스킹됨
    if "**" in birth:
        return birth
    
    # YYYY-MM-DD 형식 추출
    match = re.match(r'(\d{4})', birth)
    if match:
        return f"{match.group(1)}-**-**"
    
    return birth


def mask_salary(salary: Any) -> str:
    """
    급여 마스킹 (뒷자리 2개)
    예: 5000 → 50**
    """
    try:
        salary_str = str(int(float(salary)))
        if len(salary_str) > 2:
            return salary_str[:-2] + "**"
        return salary_str
    except (ValueError, TypeError):
        return str(salary)


def mask_name(name: str) -> str:
    """
    이름 마스킹
    예: 김철수 → 김*수
    """
    if not isinstance(name, str):
        return str(name)
    
    name = str(name).strip()
    
    # 이미 마스킹됨
    if "*" in name:
        return name
    
    if len(name) <= 2:
        return name[0] + "*"
    
    return name[0] + "*" * (len(name) - 2) + name[-1]


def mask_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame의 민감 정보 자동 마스킹
    
    자동 감지 컬럼명:
    - 전화, 전화번호, phone, tel → mask_phone
    - 생년월일, 생일, birthday → mask_birth_date
    - 급여, 연봉, salary → mask_salary
    - 이름, 성명, name → mask_name
    """
    df_masked = df.copy()
    
    phone_cols = ['전화', '전화번호', 'phone', 'tel', '휴대폰', '핸드폰']
    birth_cols = ['생년월일', '생일', 'birthday', '출생일']
    salary_cols = ['급여', '연봉', 'salary', '기본급', '월급']
    name_cols = ['이름', '성명', 'name', '직원명']
    
    # 전화번호 마스킹
    for col in phone_cols:
        if col in df_masked.columns:
            df_masked[col] = df_masked[col].astype(str).apply(mask_phone)
    
    # 생년월일 마스킹
    for col in birth_cols:
        if col in df_masked.columns:
            df_masked[col] = df_masked[col].astype(str).apply(mask_birth_date)
    
    # 급여 마스킹
    for col in salary_cols:
        if col in df_masked.columns:
            df_masked[col] = df_masked[col].apply(mask_salary)
    
    # 이름 마스킹
    for col in name_cols:
        if col in df_masked.columns:
            df_masked[col] = df_masked[col].astype(str).apply(mask_name)
    
    return df_masked


def mask_error_dict(error: Dict) -> Dict:
    """
    에러 딕셔너리의 민감 정보 마스킹
    
    예:
    {
        'row': 0,
        'column': '전화',
        'original_value': '01012345678',
        'error': '형식 오류'
    }
    →
    {
        'row': 0,
        'column': '전화',
        'original_value': '010-****-5678',  # 마스킹됨
        'error': '형식 오류'
    }
    """
    masked = error.copy()
    
    if 'original_value' in masked:
        col_name = masked.get('column', '').lower()
        value = str(masked['original_value'])
        
        if any(x in col_name for x in ['전화', 'phone', 'tel']):
            masked['original_value'] = mask_phone(value)
        elif any(x in col_name for x in ['생년', '생일', 'birth']):
            masked['original_value'] = mask_birth_date(value)
        elif any(x in col_name for x in ['급여', '연봉', 'salary']):
            masked['original_value'] = mask_salary(value)
        elif any(x in col_name for x in ['이름', 'name']):
            masked['original_value'] = mask_name(value)
    
    return masked


def mask_error_list(errors: List[Dict]) -> List[Dict]:
    """에러 목록 마스킹"""
    return [mask_error_dict(e) for e in errors]
