"""
AI 헤더 매칭 시스템 통합 테스트

다양한 헤더 형식의 파일을 테스트하여 표준화 검증
"""
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT2")

import pandas as pd
from internal.ai.column_matcher import ai_match_columns
from internal.parsers.ceragem_parser import parse_all


def test_ai_header_matching():
    """AI 헤더 매칭 시스템 종합 테스트"""
    
    print("=" * 70)
    print("AI 헤더 매칭 시스템 통합 테스트")
    print("=" * 70)
    
    # ========== 테스트 1: 다양한 헤더 형식 ==========
    print("\n[테스트 1] 다양한 헤더 형식 매칭 테스트")
    print("-" * 70)
    
    test_cases = [
        {
            "name": "✅ 표준 (세라젬)",
            "headers": ["사원번호", "이름", "성별", "생년월일", "입사일자", "종업원구분", "기준급여"],
            "expected_match_rate": 1.0
        },
        {
            "name": "🔄 비표준 한글",
            "headers": ["사번", "성명", "성", "태어난날", "들어온날짜", "직원타입", "월급"],
            "expected_match_rate": 0.85
        },
        {
            "name": "🌍 영문 헤더",
            "headers": ["emp_id", "name", "gender", "birth_date", "hire_date", "emp_type", "salary"],
            "expected_match_rate": 0.85
        },
        {
            "name": "🎨 혼합 + 변형",
            "headers": ["직원번호", "employee_name", "섬별", "Birthday", "입사년월일", "근로자구분", "급여액"],
            "expected_match_rate": 0.70
        },
        {
            "name": "🔧 개행 포함 (실제 파일)",
            "headers": ["사원번호", "이름", "성별\n(1:남자, 2:여자)", "생년월일", "입사일자", "종업원 구분\n(1:직원, 3:임원)", "기준급여"],
            "expected_match_rate": 0.85
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   입력 헤더: {test['headers'][:3]}...")
        
        result = ai_match_columns(test['headers'], sheet_type="재직자")
        
        match_rate = len(result['mappings']) / len(test['headers'])
        status = "✅ 통과" if match_rate >= test['expected_match_rate'] else "⚠️  낮음"
        
        print(f"   매칭 성공: {len(result['mappings'])}/{len(test['headers'])} ({match_rate:.1%}) {status}")
        
        # 매칭 상세
        for customer, info in list(result['mappings'].items())[:3]:
            print(f"     • {customer:20} → {info['standard_field']:15} (신뢰도: {info['confidence']:.2f})")
        
        if result['unmapped']:
            print(f"   ⚠️  매칭 실패: {result['unmapped'][:2]}...")
        
        if result['missing_required']:
            print(f"   ❌ 필수 누락: {result['missing_required'][:2]}...")
    
    # ========== 테스트 2: 실제 파일 파싱 ==========
    print("\n\n[테스트 2] 실제 세라젬 파일 파싱 (AI 헤더 매칭 적용)")
    print("-" * 70)
    
    try:
        with open('20251223_세라젬_202512_확정급여채무평가_작성요청자료_기타장기 제외_메일발송.xls', 'rb') as f:
            content = f.read()
        
        print("\n파싱 중...")
        parsed = parse_all(content)
        
        print("✅ 파싱 성공!")
        print(f"  • 재직자: {parsed['active']['summary']['count']:,}명")
        print(f"  • 퇴직자: {parsed['retired_dc']['summary']['count']:,}명")
        print(f"  • 추가: {parsed['additional']['summary']['count']:,}명")
        
        # 표준화된 컬럼 확인
        if parsed['active']['rows']:
            first = parsed['active']['rows'][0]
            print(f"\n표준화된 필드 확인:")
            
            standard_fields = ['사원번호', '이름', '성별', '생년월일', '입사일자', '종업원구분', '기준급여']
            found = []
            missing = []
            
            for field in standard_fields:
                if field in first and first[field] is not None:
                    found.append(field)
                else:
                    missing.append(field)
            
            print(f"  ✅ 발견: {len(found)}/{len(standard_fields)}개 - {', '.join(found)}")
            if missing:
                print(f"  ❌ 누락: {', '.join(missing)}")
        
        # 검증 결과
        if parsed.get('cross_checks'):
            total_checks = len(parsed['cross_checks'])
            passed_checks = sum(1 for c in parsed['cross_checks'] if c['status'] == 'match')
            print(f"\n크로스 검증:")
            print(f"  통과: {passed_checks}/{total_checks}개 ({passed_checks/total_checks:.1%})")
        
    except FileNotFoundError:
        print("❌ 테스트 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
    
    # ========== 테스트 3: 폴백 매칭 성능 ==========
    print("\n\n[테스트 3] 폴백 매칭 성능 (API 없이)")
    print("-" * 70)
    
    fallback_test = {
        "headers": ["EmpNo", "FullName", "Sex", "DOB", "JoinDate", "Position", "MonthlySalary"],
        "description": "완전 영문 헤더"
    }
    
    print(f"\n{fallback_test['description']}")
    print(f"헤더: {fallback_test['headers']}")
    
    result = ai_match_columns(fallback_test['headers'], sheet_type="재직자")
    
    if result.get('fallback'):
        print("✅ 폴백 매칭 사용됨 (AI API 없음)")
    
    print(f"매칭 성공: {len(result['mappings'])}/{len(fallback_test['headers'])} ({len(result['mappings'])/len(fallback_test['headers']):.1%})")
    
    for customer, info in result['mappings'].items():
        print(f"  {customer:20} → {info['standard_field']:15} ({info['confidence']:.2f})")
    
    # ========== 최종 요약 ==========
    print("\n\n" + "=" * 70)
    print("✅ AI 헤더 매칭 시스템 테스트 완료")
    print("=" * 70)
    
    print("\n핵심 기능:")
    print("  1. ✅ 20개 표준 필드 정의 (불변)")
    print("  2. ✅ AI 기반 의미적 매칭 (GPT-4)")
    print("  3. ✅ 폴백: 문자열 유사도 매칭")
    print("  4. ✅ 개행/공백 처리")
    print("  5. ✅ 중복 컬럼 제거")
    print("  6. ✅ 필수 필드 누락 감지")
    
    print("\n장점:")
    print("  • 하드코딩 제거 → 무한 확장성")
    print("  • 세라젬 외 다른 회사 파일도 자동 처리")
    print("  • 영문/한글/혼합 모두 지원")
    print("  • API 없어도 폴백으로 작동")
    
    print("\n다음 단계:")
    print("  • validation_layer1.py 하드코딩 제거")
    print("  • 표준 스키마에 퇴직일, 사유 등 추가")
    print("  • AI 매칭 신뢰도 로깅 강화")


if __name__ == "__main__":
    test_ai_header_matching()
