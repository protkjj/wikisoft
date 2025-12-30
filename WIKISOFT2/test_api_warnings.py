"""
API 경고 시스템 테스트
stdout 캡처를 통한 파싱 경고 전달 확인
"""
import sys
from io import StringIO
from internal.generators.aggregate_calculator import aggregate_from_excel


def test_stdout_capture():
    print("=" * 70)
    print("API 경고 시스템 테스트: stdout 캡처")
    print("=" * 70)
    
    # 실제 명부 파일 로드
    with open('20251223_세라젬_202512_확정급여채무평가_작성요청자료_기타장기 제외_메일발송.xls', 'rb') as f:
        roster_content = f.read()
    
    # stdout 캡처
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # 파싱 및 집계 (경고 출력됨)
        calculated = aggregate_from_excel(roster_content)
    finally:
        sys.stdout = old_stdout
    
    # 출력된 경고 추출
    output_lines = captured_output.getvalue()
    print(f"\n[캡처된 출력 ({len(output_lines)} bytes)]")
    print("-" * 70)
    print(output_lines)
    print("-" * 70)
    
    # 경고 파싱
    parsing_warnings = []
    for line in output_lines.split('\n'):
        line = line.strip()
        if line.startswith('❌'):
            parsing_warnings.append({
                "severity": "error",
                "message": line.replace('❌', '').strip()
            })
        elif line.startswith('⚠️'):
            parsing_warnings.append({
                "severity": "warning",
                "message": line.replace('⚠️', '').strip()
            })
    
    print(f"\n[추출된 경고 {len(parsing_warnings)}개]")
    for i, warning in enumerate(parsing_warnings, 1):
        severity_icon = "❌" if warning['severity'] == 'error' else "⚠️"
        print(f"{i}. {severity_icon} [{warning['severity']}] {warning['message'][:80]}...")
    
    # API 응답 형식으로 구성
    api_response = {
        "validation": {"status": "passed"},
        "calculated_aggregates": {
            "counts_I26_I39": calculated["counts_I26_I39"][:3],  # 샘플만
            "sums_I40_I51": calculated["sums_I40_I51"][:3]
        },
        "parsing_warnings": parsing_warnings,
        "session_id": "test-session-123"
    }
    
    print(f"\n[API 응답 형식]")
    import json
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    print(f"\n{'=' * 70}")
    print("✅ 테스트 완료")
    print(f"{'=' * 70}")
    print(f"캡처된 경고: {len(parsing_warnings)}개")
    print(f"- Error: {sum(1 for w in parsing_warnings if w['severity'] == 'error')}개")
    print(f"- Warning: {sum(1 for w in parsing_warnings if w['severity'] == 'warning')}개")


if __name__ == '__main__':
    test_stdout_capture()
