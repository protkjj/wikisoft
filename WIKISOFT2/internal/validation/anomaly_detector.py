import pandas as pd
import numpy as np
from typing import Dict

class AnomalyDetector:
    """column_mapping 기반 동적 이상치 탐지"""
    
    def __init__(self):
        pass
    
    def detect_anomalies(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> dict:
        """
        column_mapping을 사용한 동적 이상치 탐지
        
        Args:
            df: 원본 DataFrame
            column_mapping: {
                "salary": "기준급여",
                "retire_fund1": "당년도퇴직금추계액",
                "retire_fund2": "차년도퇴직금추계액",
                "job_type": "직종구분"
            }
        
        Returns:
            {"anomalies": [...]}
        """
        anomalies = []
        
        # 1. column_mapping에서 필요한 컬럼 동적 추출
        numeric_columns = [
            column_mapping.get("salary"),           # 기준급여
            column_mapping.get("retire_fund1"),     # 당년도퇴직금추계액
            column_mapping.get("retire_fund2")      # 차년도퇴직금추계액
        ]
        
        # None 값 제거 + DataFrame에 실제 존재하는지 확인
        numeric_columns = [
            col for col in numeric_columns 
            if col is not None and col in df.columns
        ]
        
        # 직급 컬럼
        job_col = column_mapping.get("job_type")  # 직종구분
        
        # 2. 직급별로 그룹화
        if job_col and job_col in df.columns:
            for job_type in df[job_col].unique():
                job_df = df[df[job_col] == job_type]
                
                # 최소 5명 이상이어야 통계 의미 있음
                if len(job_df) < 5:
                    continue
                
                # 3. 각 숫자 컬럼에 대해 mean ± 2σ 적용
                for col in numeric_columns:
                    try:
                        values = pd.to_numeric(job_df[col], errors='coerce').dropna()
                        
                        if len(values) > 2:
                            mean = values.mean()
                            std = values.std()
                            lower = mean - 2 * std
                            upper = mean + 2 * std
                            
                            # 4. 이상치 찾기
                            for idx, val in values.items():
                                if val < lower or val > upper:
                                    anomalies.append({
                                        "row": idx,
                                        "column": col,
                                        "job_type": job_type,
                                        "value": val,
                                        "mean": mean,
                                        "std": std,
                                        "lower_bound": lower,
                                        "upper_bound": upper,
                                        "severity": "warning"
                                    })
                    except Exception as e:
                        print(f"이상치 탐지 오류 ({col}): {e}")
        
        return {"anomalies": anomalies}
