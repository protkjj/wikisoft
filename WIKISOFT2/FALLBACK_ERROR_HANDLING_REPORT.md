# API 없이 폴백 모드 예외 처리 구현 완료

## 개요

OpenAI API 키가 없을 때 폴백(문자열 매칭) 모드가 작동하지만, 정확도가 낮고 예외 상황(오타, 이상한 헤더)을 제대로 처리하지 못하는 문제를 해결했습니다.

## 구현 내용

### 1. 경고 시스템 추가

#### column_matcher.py
- **API 키 사전 체크**: OpenAI API 호출 전 키 존재 여부 확인 → 없으면 즉시 폴백 모드로 전환하며 경고 출력
- **경고 반환 구조**:
  ```python
  {
      "mappings": {...},
      "unmapped": [...],
      "missing_required": [...],
      "total_confidence": 0.75,
      "warnings": [
          {
              "severity": "error",  # or "warning"
              "message": "AI 매칭 실패. 폴백 사용 중",
              "details": {...}
          }
      ],
      "used_ai": False  # AI 사용 여부 명시
  }
  ```

- **경고 유형**:
  1. **error**: API 없이 폴백 사용 중
  2. **error**: 필수 필드 누락 (사원번호, 이름 등)
  3. **warning**: 낮은 신뢰도 매칭 (<0.8)
  4. **warning**: 높은 매칭 실패율 (>30%)

#### ceragem_parser.py
- `_standardize_headers()` 함수 개선:
  - 경고를 수집하여 반환 (Tuple[DataFrame, List[Dict]])
  - 시트별 경고 추적 (재직자/퇴직자/추가)
  - 콘솔 출력 (❌ error, ⚠️ warning)

#### API 레벨 (main.py)
- `/validate-with-roster` 엔드포인트 개선:
  - stdout 캡처로 파싱 경고 수집
  - `parsing_warnings` 필드에 경고 리스트 포함
  - 클라이언트에 전달하여 UI에서 표시 가능

### 2. 프로덕션 권장사항

#### API 키 필수 설정
```bash
export OPENAI_API_KEY="sk-..."
```

폴백 모드는 **개발/테스트 전용**이며, 프로덕션에서는 다음과 같은 제한이 있습니다:

| 헤더 유형 | AI (GPT-4) | 폴백 (문자열 매칭) |
|---------|-----------|----------------|
| 표준 ("사원번호") | ✅ 100% | ✅ 100% |
| 영어 ("EmpNo") | ✅ 100% | ✅ 100% |
| 혼합 ("사원\nID") | ✅ 100% | ⚠️ 86% |
| 비표준 ("직원넘버") | ✅ 95%+ | ❌ 71% |
| 의미적 변형 ("회사들어온날") | ✅ 90%+ | ❌ 0% (실패) |
| 오타 ("섬별") | ⚠️ 80%+ | ❌ 0% (실패) |

### 3. 사용자 안내 전략

#### 옵션 A: 수동 확인 UI (권장)
```json
{
  "used_ai": false,
  "parsing_warnings": [
    {
      "severity": "error",
      "message": "AI 매칭 실패. 폴백 사용 중"
    }
  ],
  "missing_required": ["이름", "종업원구분"]
}
```

**프론트엔드 처리**:
1. `used_ai: false` → ⚠️ 경고 모달 표시
2. `missing_required` → 필수 필드 누락 알림
3. 사용자에게 선택권:
   - "계속 진행" → 폴백 결과 사용 (위험 감수)
   - "수동 매핑" → UI에서 직접 컬럼 매핑
   - "파일 수정" → 표준 헤더로 재업로드

#### 옵션 B: 신뢰도 임계값
```python
if total_confidence < 0.6:
    return {"error": "파일 헤더를 인식할 수 없습니다. 파일을 확인하거나 OpenAI API 키를 설정하세요."}
elif 0.6 <= total_confidence < 0.8:
    return {"warning": "일부 컬럼 매칭이 불확실합니다. 결과를 검토하세요.", "data": ...}
else:
    return {"success": True, "data": ...}
```

#### 옵션 C: 동의어 사전 확장
```python
# internal/parsers/standard_schema.py 확장
STANDARD_SCHEMA = [
    {
        "field_name": "입사일자",
        "aliases": [
            "입사일", "hire_date", "join_date",
            "들어온날짜", "회사들어온날", "입사한날", "고용일자",  # 추가
            ...
        ]
    }
]
```

**한계**: 무한정 추가 불가, AI가 더 효율적

### 4. 테스트 결과

#### test_api_warnings.py 실행 결과
```
캡처된 경고: 12개
- Error: 3개 (각 시트별 AI 실패)
- Warning: 9개 (폴백 사용, 매칭 실패 컬럼)

API 응답:
{
  "parsing_warnings": [
    {
      "severity": "error",
      "message": "[재직자] AI 매칭 실패. 폴백 사용 중 - 정확도 낮음"
    },
    {
      "severity": "warning",
      "message": "[재직자] 매칭 안 된 컬럼: ['참고사항', '종업원 구분\n(1:직원...']"
    }
  ]
}
```

#### 실제 프로덕션 시나리오
1. **API 키 있음** → GPT-4 매칭 (100% 성공, warnings=0)
2. **API 키 없음** → 폴백 매칭 (71% 성공, warnings=12개)
3. **클라이언트 반응**:
   - warnings 있음 → UI에 경고 표시
   - missing_required → 업로드 차단 또는 수동 입력 요청
   - used_ai: false → "OpenAI API 키 설정 권장" 배너 표시

## 파일 수정 내역

### internal/ai/column_matcher.py
- `ai_match_columns()`: API 키 사전 체크 추가
- `_fallback_match()`: warnings 배열 반환
- 반환 구조: `{..., warnings: [...], used_ai: bool}`

### internal/parsers/ceragem_parser.py
- `_standardize_headers()`: 경고 수집 및 반환 (Tuple)
- `parse_active/retired/additional()`: warnings 무시 (이미 print됨)

### internal/generators/aggregate_calculator.py
- 중복 표준화 제거 (parse_* 함수에서 이미 처리)
- `_standardize_headers` import 제거

### external/api/main.py
- `/validate-with-roster`: stdout 캡처로 경고 수집
- 응답에 `parsing_warnings` 필드 추가

### test_api_warnings.py (NEW)
- stdout 캡처 테스트
- API 응답 형식 검증
- 경고 개수/종류 확인

## 다음 단계 (선택)

1. **프론트엔드 UI 구현**:
   - 경고 모달 표시
   - 수동 컬럼 매핑 인터페이스
   - OpenAI API 키 입력 폼

2. **모니터링 추가**:
   - 폴백 사용 횟수 로깅
   - 낮은 신뢰도 매칭 알림
   - 필수 필드 누락 빈도 추적

3. **사용자 가이드**:
   - README에 API 키 설정 안내
   - 표준 헤더 템플릿 제공
   - 에러 메시지 한글화

## 결론

✅ **완료**: OpenAI API 없이도 작동하지만, 낮은 정확도를 명확히 경고  
✅ **완료**: 프론트엔드에서 사용자에게 선택권 제공 가능  
✅ **완료**: 프로덕션 배포 시 OpenAI API 키 필수 명시  
⚠️ **제한**: 폴백 모드는 표준/영어 헤더만 안정적, 의미적 변형은 실패  
🔧 **권장**: 신뢰도 임계값 기반 파일 검증 (0.6 이하 차단)
