"""
기존 데이터 파일에서 패턴을 분석하고 규칙을 학습하는 스크립트.
"""
import os
import sys
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from internal.ai.knowledge_base import add_error_rule, learn_from_correction, load_error_rules
from internal.parsers.parser import parse_roster
from internal.ai.matcher import match_headers


def analyze_file(file_path: str) -> Dict[str, Any]:
    """파일 분석해서 데이터 패턴 추출"""
    print(f"\n{'='*60}")
    print(f"📂 분석 중: {os.path.basename(file_path)}")
    print('='*60)
    
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    # 파싱
    parsed = parse_roster(file_bytes)
    headers = parsed.get("headers", [])
    rows = parsed.get("rows", [])
    
    print(f"  행 수: {len(rows)}, 컬럼 수: {len(headers)}")
    
    if not rows:
        return {"status": "empty"}
    
    # 매칭
    matches = match_headers(parsed, sheet_type="재직자")
    match_list = matches.get("matches", [])
    
    # 매핑 구성
    mapping = {}
    for m in match_list:
        if m.get("target"):
            mapping[m["source"]] = m["target"]
    
    print(f"  매핑된 컬럼: {len(mapping)}개")
    
    # DataFrame 생성
    df = pd.DataFrame(rows, columns=headers)
    
    # 표준 컬럼 추가
    for orig, std in mapping.items():
        if orig in df.columns:
            df[std] = df[orig]
    
    patterns = {
        "filename": os.path.basename(file_path),
        "row_count": len(rows),
        "mapped_columns": list(mapping.keys()),
        "statistics": {},
        "detected_patterns": []
    }
    
    # 각 필드별 통계 분석
    for std_col in ["생년월일", "입사일자", "기준급여", "성별", "종업원구분"]:
        if std_col not in df.columns:
            continue
            
        col_data = df[std_col].dropna()
        if len(col_data) == 0:
            continue
        
        stats = {"field": std_col, "count": len(col_data)}
        
        # 생년월일 분석
        if std_col == "생년월일":
            try:
                # 숫자형 연도 추출 시도
                years = []
                for val in col_data:
                    try:
                        if isinstance(val, (int, float)) and val > 10000:
                            # Excel 날짜 또는 YYYYMMDD
                            year = int(str(int(val))[:4])
                            if 1900 <= year <= 2100:
                                years.append(year)
                        elif isinstance(val, str) and len(val) >= 4:
                            year = int(val[:4])
                            if 1900 <= year <= 2100:
                                years.append(year)
                    except:
                        pass
                
                if years:
                    min_year = min(years)
                    max_year = max(years)
                    stats["min_year"] = min_year
                    stats["max_year"] = max_year
                    stats["age_range"] = f"{2026 - max_year}세 ~ {2026 - min_year}세"
                    print(f"  📅 {std_col}: {min_year}년 ~ {max_year}년 ({stats['age_range']})")
                    
                    # 패턴 기록
                    if min_year < 1945:
                        patterns["detected_patterns"].append({
                            "type": "age_range",
                            "field": "생년월일",
                            "observation": f"최고령 {2026-min_year}세 존재",
                            "min_year": min_year
                        })
            except Exception as e:
                print(f"    ⚠️ 생년월일 분석 실패: {e}")
        
        # 기준급여 분석
        elif std_col == "기준급여":
            try:
                salaries = pd.to_numeric(col_data, errors='coerce').dropna()
                if len(salaries) > 0:
                    min_sal = salaries.min()
                    max_sal = salaries.max()
                    avg_sal = salaries.mean()
                    stats["min"] = float(min_sal)
                    stats["max"] = float(max_sal)
                    stats["avg"] = float(avg_sal)
                    print(f"  💰 {std_col}: {min_sal:,.0f}원 ~ {max_sal:,.0f}원 (평균: {avg_sal:,.0f}원)")
                    
                    # 패턴 기록
                    if min_sal < 1900000 and min_sal > 0:
                        patterns["detected_patterns"].append({
                            "type": "salary_range",
                            "field": "기준급여",
                            "observation": f"최저임금 미달 급여 존재 ({min_sal:,.0f}원)",
                            "min_salary": float(min_sal)
                        })
            except Exception as e:
                print(f"    ⚠️ 기준급여 분석 실패: {e}")
        
        # 성별 분석
        elif std_col == "성별":
            try:
                unique_vals = col_data.unique()
                stats["unique_values"] = [str(v) for v in unique_vals]
                print(f"  👥 {std_col}: {unique_vals}")
            except:
                pass
        
        # 종업원구분 분석
        elif std_col == "종업원구분":
            try:
                value_counts = col_data.value_counts().to_dict()
                stats["distribution"] = {str(k): int(v) for k, v in value_counts.items()}
                print(f"  👔 {std_col}: {value_counts}")
            except:
                pass
        
        patterns["statistics"][std_col] = stats
    
    return patterns


def learn_patterns_from_analysis(all_patterns: List[Dict]) -> int:
    """분석 결과에서 규칙 학습"""
    learned_count = 0
    
    # 1. 급여 범위 패턴 학습
    salary_mins = []
    for p in all_patterns:
        if "기준급여" in p.get("statistics", {}):
            stats = p["statistics"]["기준급여"]
            if "min" in stats and stats["min"] > 0:
                salary_mins.append(stats["min"])
    
    if salary_mins:
        actual_min = min(salary_mins)
        if actual_min < 1900000:
            # 실제 데이터에 최저임금 미달 급여가 있으면, 이는 계약직/파트타임일 가능성
            learn_from_correction(
                field="기준급여",
                original_value=str(int(actual_min)),
                was_error=True,
                correct_interpretation=f"실제 데이터에 {actual_min:,.0f}원 급여 존재 - 계약직/파트타임 가능성",
                diagnostic_context={"실제_최저급여": actual_min}
            )
            learned_count += 1
            print(f"\n✅ 학습: 기준급여 {actual_min:,.0f}원 패턴")
    
    # 2. 연령 범위 패턴 학습
    min_years = []
    for p in all_patterns:
        if "생년월일" in p.get("statistics", {}):
            stats = p["statistics"]["생년월일"]
            if "min_year" in stats:
                min_years.append(stats["min_year"])
    
    if min_years:
        oldest_year = min(min_years)
        oldest_age = 2026 - oldest_year
        if oldest_age > 75:
            learn_from_correction(
                field="생년월일",
                original_value=str(oldest_year),
                was_error=True,
                correct_interpretation=f"실제 데이터에 {oldest_age}세 직원 존재 - 임원/고문 가능성",
                diagnostic_context={"실제_최고령": oldest_age}
            )
            learned_count += 1
            print(f"✅ 학습: 최고령 {oldest_age}세 패턴")
    
    # 3. 종업원구분 분포 학습
    emp_types = set()
    for p in all_patterns:
        if "종업원구분" in p.get("statistics", {}):
            stats = p["statistics"]["종업원구분"]
            if "distribution" in stats:
                emp_types.update(stats["distribution"].keys())
    
    if emp_types:
        print(f"\n📋 발견된 종업원구분: {emp_types}")
    
    return learned_count


def main():
    data_dir = "/Users/kj/Desktop/wiki/data"
    
    # 현재 규칙 수
    current_rules = load_error_rules()
    print(f"📚 현재 규칙 수: {len(current_rules)}개")
    
    # 모든 Excel 파일 분석
    all_patterns = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith(('.xls', '.xlsx')) and not filename.startswith('~'):
            file_path = os.path.join(data_dir, filename)
            try:
                patterns = analyze_file(file_path)
                if patterns.get("status") != "empty":
                    all_patterns.append(patterns)
            except Exception as e:
                print(f"  ❌ 분석 실패: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 총 {len(all_patterns)}개 파일 분석 완료")
    print('='*60)
    
    # 패턴 학습
    learned = learn_patterns_from_analysis(all_patterns)
    
    # 결과 요약
    final_rules = load_error_rules()
    print(f"\n📚 최종 규칙 수: {len(final_rules)}개 (+{len(final_rules) - len(current_rules)})")
    print(f"✅ 학습된 패턴: {learned}개")


if __name__ == "__main__":
    main()
