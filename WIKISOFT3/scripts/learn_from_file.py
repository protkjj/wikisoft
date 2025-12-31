#!/usr/bin/env python3
"""
파일에서 학습: 검증 후 케이스로 저장

사용법:
    python scripts/learn_from_file.py <파일경로>
    python scripts/learn_from_file.py --all  # test_files 폴더 전체
"""

import sys
import os

# WIKISOFT3 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pandas as pd
from internal.parsers.parser import parse_roster
from internal.ai.matcher import match_headers
from internal.validators.validation_layer1 import validate_layer1
from internal.agent.confidence import estimate_confidence, detect_anomalies
from internal.memory.case_store import CaseStore


def parsed_to_dataframe(parsed: dict) -> pd.DataFrame:
    """parsed dict를 DataFrame으로 변환."""
    headers = parsed.get("headers", [])
    rows = parsed.get("rows", [])
    return pd.DataFrame(rows, columns=headers)


def learn_from_file(file_path: str, auto_approve: bool = True):
    """
    파일에서 학습하여 케이스로 저장.
    
    Args:
        file_path: Excel/CSV 파일 경로
        auto_approve: 자동 승인 여부 (True면 사람 검토 없이 저장)
    """
    print(f"\n{'='*60}")
    print(f"📚 학습 시작: {Path(file_path).name}")
    print(f"{'='*60}")
    
    # 1. 파일 읽기
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    # 2. 파싱
    print("\n[1/5] 파싱 중...")
    parsed = parse_roster(file_bytes)
    headers = parsed.get("headers", [])
    row_count = len(parsed.get("rows", []))
    print(f"    ✅ 헤더: {len(headers)}개, 행: {row_count}개")
    print(f"    📋 헤더: {headers[:5]}{'...' if len(headers) > 5 else ''}")
    
    # 3. 헤더 매칭
    print("\n[2/5] 헤더 매칭 중...")
    matches_result = match_headers(parsed)  # parsed dict 전달
    matches = matches_result.get("matches", [])
    used_ai = matches_result.get("used_ai", False)
    print(f"    ✅ 매칭: {len(matches)}개, AI 사용: {used_ai}")
    
    # 매칭 결과 상세
    mapped = [m for m in matches if m.get("target") and not m.get("unmapped")]
    unmapped = [m for m in matches if m.get("unmapped") or not m.get("target")]
    low_conf = [m for m in matches if m.get("target") and m.get("confidence", 0) < 0.7]
    
    print(f"    📊 매핑됨: {len(mapped)}, 미매핑: {len(unmapped)}, 낮은 신뢰도: {len(low_conf)}")
    
    if unmapped:
        print(f"    ⚠️ 미매핑: {[m['source'] for m in unmapped[:5]]}")
    
    if low_conf:
        print(f"    ⚠️ 낮은 신뢰도:")
        for m in low_conf[:3]:
            print(f"       - {m['source']} → {m['target']} ({m['confidence']:.0%})")
    
    # 4. 검증
    print("\n[3/5] L1 검증 중...")
    df = parsed_to_dataframe(parsed)
    validation = validate_layer1(df, {})  # diagnostic_answers는 빈 dict
    errors = validation.get("errors", [])
    warnings = validation.get("warnings", [])
    print(f"    ✅ 에러: {len(errors)}개, 경고: {len(warnings)}개")
    
    # 5. 신뢰도 계산
    print("\n[4/5] 신뢰도 계산 중...")
    confidence = estimate_confidence(parsed, matches_result, validation)
    anomalies = detect_anomalies(parsed, matches_result, validation)
    
    conf_score = confidence.get("score", 0)
    print(f"    ✅ 신뢰도: {conf_score:.1%}")
    print(f"    📊 요인: {confidence.get('factors', {})}")
    
    if anomalies.get("detected"):
        print(f"    ⚠️ 이상 탐지: {len(anomalies.get('anomalies', []))}개")
        for a in anomalies.get("anomalies", []):
            print(f"       - [{a['severity']}] {a['message']}")
    
    # 6. 케이스 저장
    print("\n[5/5] 케이스 저장 중...")
    store = CaseStore()
    
    # 파일명에서 회사명 추출
    filename = Path(file_path).name
    company_name = filename.split("_")[1] if "_" in filename else filename
    
    case_id = store.save_case(
        headers=headers,
        matches=matches,
        confidence=conf_score,
        was_auto_approved=auto_approve,
        human_corrections=None,  # 나중에 수동 수정 시 업데이트
        metadata={
            "filename": filename,
            "company_name": company_name,
            "row_count": row_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "anomaly_count": len(anomalies.get("anomalies", [])),
        }
    )
    
    print(f"    ✅ 저장 완료: case_id={case_id}")
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"📊 학습 결과 요약")
    print(f"{'='*60}")
    print(f"  회사명: {company_name}")
    print(f"  헤더: {len(headers)}개")
    print(f"  매핑 성공률: {len(mapped)/len(matches)*100:.1f}%" if matches else "  매핑: N/A")
    print(f"  신뢰도: {conf_score:.1%}")
    print(f"  자동 승인: {'예' if auto_approve else '아니오'}")
    print(f"  케이스 ID: {case_id}")
    
    # 통계 출력
    stats = store.index.get("stats", {})
    print(f"\n📈 전체 통계:")
    print(f"  총 케이스: {stats.get('total_cases', 0)}개")
    print(f"  자동 승인: {stats.get('auto_approved', 0)}개")
    print(f"  수동 수정: {stats.get('manual_corrected', 0)}개")
    
    return {
        "case_id": case_id,
        "confidence": conf_score,
        "headers": len(headers),
        "mapped": len(mapped),
        "unmapped": len(unmapped),
    }


def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/learn_from_file.py <파일경로>")
        print("        python scripts/learn_from_file.py --all")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        # test_files 폴더 전체 학습
        test_dir = Path(__file__).parent.parent / "test_files"
        files = list(test_dir.glob("*.xls*")) + list(test_dir.glob("*.csv"))
        
        print(f"\n🗂️ {len(files)}개 파일 학습 시작")
        
        results = []
        for file_path in files:
            try:
                result = learn_from_file(str(file_path))
                results.append(result)
            except Exception as e:
                print(f"❌ 실패: {file_path.name} - {e}")
        
        print(f"\n✅ 완료: {len(results)}/{len(files)}개 파일 학습됨")
    else:
        # 단일 파일 학습
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            sys.exit(1)
        
        learn_from_file(file_path)


if __name__ == "__main__":
    main()
