"""
명부 데이터에서 (1-2) 기초자료 집계값 자동 계산

집계 로직:
1. 재직자 명부 (2-2):
   - 종업원 구분: 1,2 = 직원(I27), 3 = 임원(I26), 4 = 계약직(I28)
   - 인원수 카운트 → I26-I28
   - 당년도 퇴직금 합계 → 금액 계산에 사용
   - 차년도 퇴직금 합계 → 금액 계산에 사용

2. 퇴직자 명부 (2-3):
   - 사유별 필터링:
     * '퇴직금정산' → 퇴직자 (I30-I32)
     * '중간정산' → 중간정산자 (I34)
     * 'DC전환' → DC전환자 (I35)
   - 종업원 구분으로 임원/직원/계약직 분류
   - 퇴직금 합계 → I41

3. 추가 명부 (2-4):
   - 사유별 금액 집계
   - 관계사 전입/전출, 사업결합/처분 등
"""

from typing import Dict, Any, Optional
import pandas as pd
from internal.parsers.ceragem_parser import parse_all


def aggregate_from_dataframes(
    df_active: pd.DataFrame,
    df_retired: Optional[pd.DataFrame] = None,
    df_additional: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    명부 데이터프레임들로부터 (1-2) 기초자료 집계값 계산
    
    Args:
        df_active: 재직자 명부 (2-2)
        df_retired: 퇴직자/DC전환자 명부 (2-3), optional
        df_additional: 추가 명부 (2-4), optional
        
    Returns:
        집계 결과 딕셔너리 {
            'counts_I26_I39': [...],  # 인원수 집계
            'sums_I40_I51': [...],    # 금액 집계
            'formulas_validated': True/False
        }
    """
    result = {
        'counts_I26_I39': [None] * 14,  # I26-I39
        'sums_I40_I51': [None] * 12,    # I40-I51
        'details': {}
    }
    
    # ===== 재직자 명부 집계 =====
    if df_active is not None and not df_active.empty:
        # 이미 parse_active()에서 표준화됨
        # 종업원 구분 컬럼 찾기
        emp_type_col = None
        for col in df_active.columns:
            if '종업원' in str(col) or ('구분' in str(col) and '제도' not in str(col)):
                emp_type_col = col
                break
        
        if emp_type_col:
            # 종업원 구분별 카운트
            emp_counts = df_active[emp_type_col].value_counts()
            
            # I26: 임원 (3)
            result['counts_I26_I39'][0] = float(emp_counts.get(3, 0))
            
            # I27: 직원 (1 + 2)
            result['counts_I26_I39'][1] = float(
                emp_counts.get(1, 0) + emp_counts.get(2, 0)
            )
            
            # I28: 계약직 (4)
            result['counts_I26_I39'][2] = float(emp_counts.get(4, 0))
            
            # I29: 재직자 합계
            result['counts_I26_I39'][3] = (
                result['counts_I26_I39'][0] + 
                result['counts_I26_I39'][1] + 
                result['counts_I26_I39'][2]
            )
        
        # 당년도/차년도 퇴직금 합계
        당년도_col = None
        차년도_col = None
        for col in df_active.columns:
            if '당년도' in str(col) and '퇴직금' in str(col):
                당년도_col = col
            if '차년도' in str(col) and '퇴직금' in str(col):
                차년도_col = col
        
        당년도_합계 = 0
        차년도_합계 = 0
        if 당년도_col:
            당년도_합계 = df_active[당년도_col].fillna(0).sum()
        if 차년도_col:
            차년도_합계 = df_active[차년도_col].fillna(0).sum()
        
        result['details']['active_sum_this_year'] = 당년도_합계
        result['details']['active_sum_next_year'] = 차년도_합계
    
    # ===== 퇴직자 명부 집계 =====
    if df_retired is not None and not df_retired.empty:
        # 이미 parse_retired_dc()에서 표준화됨
        # 사유 컬럼 찾기
        reason_col = None
        for col in df_retired.columns:
            if '사유' in str(col):
                reason_col = col
                break
        
        if reason_col:
            # 퇴직금정산 필터링
            퇴직자 = df_retired[df_retired[reason_col].astype(str).str.contains('퇴직금정산', na=False)]
            중간정산자 = df_retired[df_retired[reason_col].astype(str).str.contains('중간정산', na=False)]
            DC전환자 = df_retired[df_retired[reason_col].astype(str).str.contains('DC전환', na=False)]
            
            # I30-I32: 퇴직자 종업원 구분별 카운트
            emp_type_col = None
            for col in 퇴직자.columns:
                if '종업원' in str(col):
                    emp_type_col = col
                    break
            
            if emp_type_col and not 퇴직자.empty:
                emp_counts = 퇴직자[emp_type_col].value_counts()
                result['counts_I26_I39'][4] = float(emp_counts.get(3, 0))  # I30: 임원
                result['counts_I26_I39'][5] = float(emp_counts.get(1, 0) + emp_counts.get(2, 0))  # I31: 직원
                result['counts_I26_I39'][6] = float(emp_counts.get(4, 0))  # I32: 계약직
                result['counts_I26_I39'][7] = float(len(퇴직자))  # I33: 합계
            
            # I34: 중간정산자수
            result['counts_I26_I39'][8] = float(len(중간정산자))
            
            # I35: DC전환자수
            result['counts_I26_I39'][9] = float(len(DC전환자))
            
            # I36-I39: 퇴직금 추계액 (향후 구현)
            # TODO: 명부에서 퇴직금 추계액 정보 추출 필요
            result['counts_I26_I39'][10] = 0.0  # I36: 임원 추계액
            result['counts_I26_I39'][11] = 0.0  # I37: 직원 추계액
            result['counts_I26_I39'][12] = 0.0  # I38: 계약직 추계액
            result['counts_I26_I39'][13] = 0.0  # I39: 합계
            
            # I41: 퇴직금 (a) - 퇴직금정산 금액 합계
            퇴직금_col = None
            for col in 퇴직자.columns:
                if '퇴직금' in str(col):
                    퇴직금_col = col
                    break
            
            if 퇴직금_col:
                result['sums_I40_I51'][1] = float(퇴직자[퇴직금_col].fillna(0).sum())  # I41
            else:
                result['sums_I40_I51'][1] = 0.0
            
            # I42: 중간정산금액 (b)
            if 퇴직금_col and not 중간정산자.empty:
                result['sums_I40_I51'][2] = float(중간정산자[퇴직금_col].fillna(0).sum())  # I42
            else:
                result['sums_I40_I51'][2] = 0.0
            
            # I43: DC전환금 (c)
            if 퇴직금_col and not DC전환자.empty:
                result['sums_I40_I51'][3] = float(DC전환자[퇴직금_col].fillna(0).sum())  # I43
            else:
                result['sums_I40_I51'][3] = 0.0
        else:
            # 사유 컬럼이 없으면 기본값
            for i in [1, 2, 3]:
                if result['sums_I40_I51'][i] is None:
                    result['sums_I40_I51'][i] = 0.0
    else:
        # 퇴직자 명부가 없으면 기본값
        for i in range(4, 10):
            if result['counts_I26_I39'][i] is None:
                result['counts_I26_I39'][i] = 0.0
        for i in [1, 2, 3]:
            if result['sums_I40_I51'][i] is None:
                result['sums_I40_I51'][i] = 0.0
    
    # ===== 금액 공식 계산 =====
    # I40: 빈 값
    result['sums_I40_I51'][0] = ''
    
    # I44: 급여지급액 소계 (a+b+c) = I41+I42+I43
    i41 = result['sums_I40_I51'][1] if result['sums_I40_I51'][1] is not None else 0
    i42 = result['sums_I40_I51'][2] if result['sums_I40_I51'][2] is not None else 0
    i43 = result['sums_I40_I51'][3] if result['sums_I40_I51'][3] is not None else 0
    result['sums_I40_I51'][4] = i41 + i42 + i43  # I44
    
    # I45-I50: 관계사 전입/전출, 사업결합/처분 (추가 명부에서)
    # TODO: df_additional 처리
    for i in range(5, 11):
        if result['sums_I40_I51'][i] is None:
            result['sums_I40_I51'][i] = 0.0
    
    # I51: 퇴직부채 감소(증가)액 합계 (A-B-C) = I44-I47-I50
    i44 = result['sums_I40_I51'][4]
    i47 = result['sums_I40_I51'][7]
    i50 = result['sums_I40_I51'][10]
    result['sums_I40_I51'][11] = i44 - i47 - i50  # I51
    
    return result


def aggregate_from_excel(file_content: bytes) -> Dict[str, Any]:
    """
    엑셀 파일 바이트에서 직접 집계 계산
    
    Args:
        file_content: Excel 파일의 bytes
        
    Returns:
        집계 결과 딕셔너리
    """
    # 파싱
    parsed = parse_all(file_content)
    
    # 데이터프레임 변환
    df_active = pd.DataFrame(parsed['active']['rows']) if parsed['active']['rows'] else None
    df_retired = pd.DataFrame(parsed['retired_dc']['rows']) if parsed['retired_dc']['rows'] else None
    df_additional = pd.DataFrame(parsed['additional']['rows']) if parsed['additional']['rows'] else None
    
    # 집계 계산
    return aggregate_from_dataframes(df_active, df_retired, df_additional)


def validate_aggregation(aggregated: Dict[str, Any], original: Dict[str, Any]) -> Dict[str, Any]:
    """
    계산한 집계값과 원본 파일의 집계값 비교 검증
    
    Args:
        aggregated: aggregate_from_* 함수의 결과
        original: parse_all의 'core_info' 결과
        
    Returns:
        검증 결과 {
            'formulas': [...]  # 각 공식별 검증 결과
            'overall_match': True/False
        }
    """
    results = []
    
    # I26-I28 = I29 검증
    if aggregated['counts_I26_I39'][3] is not None:
        calc = (aggregated['counts_I26_I39'][0] + 
                aggregated['counts_I26_I39'][1] + 
                aggregated['counts_I26_I39'][2])
        actual = aggregated['counts_I26_I39'][3]
        results.append({
            'formula': 'I26+I27+I28=I29',
            'calculated': calc,
            'actual': actual,
            'match': abs(calc - actual) < 1e-6
        })
    
    # I30-I32 = I33 검증
    if aggregated['counts_I26_I39'][7] is not None:
        calc = (aggregated['counts_I26_I39'][4] + 
                aggregated['counts_I26_I39'][5] + 
                aggregated['counts_I26_I39'][6])
        actual = aggregated['counts_I26_I39'][7]
        results.append({
            'formula': 'I30+I31+I32=I33',
            'calculated': calc,
            'actual': actual,
            'match': abs(calc - actual) < 1e-6
        })
    
    # 원본과 비교
    if original:
        orig_counts = original.get('counts_I25_I33', [])
        if len(orig_counts) > 8:
            for i, label in enumerate(['I26', 'I27', 'I28', 'I29', 'I30', 'I31', 'I32', 'I33']):
                if i < len(aggregated['counts_I26_I39']) and aggregated['counts_I26_I39'][i] is not None:
                    orig_idx = i + 1  # I25는 날짜이므로 +1
                    if orig_idx < len(orig_counts):
                        results.append({
                            'cell': label,
                            'calculated': aggregated['counts_I26_I39'][i],
                            'original': orig_counts[orig_idx],
                            'match': abs(aggregated['counts_I26_I39'][i] - orig_counts[orig_idx]) < 1e-6
                        })
    
    overall = all(r.get('match', False) for r in results)
    
    return {
        'formulas': results,
        'overall_match': overall,
        'total_checks': len(results),
        'passed': sum(1 for r in results if r.get('match', False))
    }
