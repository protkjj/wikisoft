# 📋 WIKISOFT2 기술 명세서

**버전**: 2.1  
**최종 업데이트**: 2025-12-26  
**상태**: Phase 2.1 완료 - 프로덕션 준비

---

## 📊 시스템 아키텍처

### 전체 구조

```
WIKISOFT2/
├── external/api/
│   └── main.py                    # FastAPI 서버 (879줄)
├── internal/
│   ├── models/
│   │   └── session.py             # 세션 관리 클래스
│   ├── parsers/
│   │   ├── standard_schema.py     # 20개 표준 필드 정의 ⭐
│   │   └── ceragem_parser.py      # Excel 파싱 + AI 매칭
│   ├── ai/
	│   │   ├── column_matcher.py      # 자연스러운 유사도 기반 헤더 매칭
	│   │   ├── diagnostic_questions.py # 24개 진단 질문 ⭐ (자동 계산 포함)
│   │   ├── prompts.py             # GPT 프롬프트
│   │   └── question_builder.py    # 챗봇 질문 생성
│   ├── processors/
│   │   ├── validation_layer1.py   # 코드 룰 검증
│   │   └── validation_layer2.py   # 교차 검증 ⭐
│   ├── generators/
│   │   ├── aggregate_calculator.py # 인원/금액 계산
│   │   └── sheet_generator.py     # Excel 출력 + 경고 ⭐
│   ├── validation/
│   │   └── anomaly_detector.py    # 이상치 탐지
│   └── utils/
│       ├── date_utils.py          # 날짜 정규화
│       ├── masking.py             # 데이터 마스킹
│       └── logging.py             # 로깅
└── tests/
    ├── test_layer2_integration.py  # Layer 2 통합 테스트 ⭐
    ├── test_ai_header_matching.py  # AI 매칭 테스트 ⭐
    └── test_api_warnings.py        # 경고 시스템 테스트 ⭐

⭐ = Phase 2에서 새로 추가/대폭 수정
```

---

## 🔌 API 엔드포인트

### 1. GET /diagnostic-questions

**목적**: 24개 진단 질문 조회

**응답**:
```json
{
  "questions": [
    {
      "id": "q21",
      "category": "headcount_aggregates",
      "question": "임원 인원이 몇 명인가요?",
      "type": "number",
      "unit": "명",
      "validate_against": "counts_I26_I39[0]"
    },
    ...
  ],
  "summary": {
    "total": 24,
    "categories": {
      "data_quality": 14,
      "headcount_aggregates": 6,
      "amount_aggregates": 4
    }
  }
}
```

### 2. POST /validate-with-roster

**목적**: 명부 파일 + 챗봇 답변 → Layer 2 교차 검증

**요청**:
```http
POST /validate-with-roster
Content-Type: multipart/form-data

file: roster.xlsx (Excel 파일)
chatbot_answers: {"q21": 20, "q22": 664, ...} (JSON 문자열)
```

**응답**:
```json
{
  "validation": {
    "status": "failed",
    "total_checks": 8,
    "passed": 5,
    "warnings": [
      {
        "question_id": "q21",
        "severity": "high",
        "message": "⭕ 명부에서 계산한 값은 17명이지만, 당신은 20명이라고 입력하셨습니다. (차이: 17.6%)",
        "user_input": "20명",
        "calculated": "17명",
        "diff": 3,
        "diff_percent": 17.6
      },
      ...
    ]
  },
  "calculated_aggregates": {
    "counts_I26_I39": [17.0, 664.0, 69.0, ...],
    "sums_I40_I51": [6789774140.0, 691876810.0, ...]
  },
  "parsing_warnings": [
    {
      "severity": "warning",
      "message": "[재직자] 폴백 매칭 사용됨 - OpenAI API 키 설정 권장"
    }
  ],
  "session_id": "abc123...",
  "message": "검증 완료"
}
```

### 3. POST /generate-with-validation

**목적**: 검증 완료된 세션으로 Excel 파일 생성

**요청**:
```http
POST /generate-with-validation
Content-Type: application/x-www-form-urlencoded

session_id=abc123
company_name=세라젬
phone=02-1234-5678
email=hr@example.com
작성기준일=20251225
```

**응답**:
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="퇴직급여채무_세라젬_20251225.xlsx"

[Excel 파일 binary]
```

**Excel 파일 내용**:
- (1-2) 퇴직급여채무 기초자료 시트
- 셀 I14 (임원 인원): 빨간 배경 + 코멘트 (차이 17.6%)
- 셀 I29 (퇴직금 합계): 노란 배경 + 코멘트 (차이 0.6%)

---

## 🗃️ 데이터 모델

### 표준 스키마 (20개 필드)

```python
STANDARD_SCHEMA = [
    {
        "field_name": "사원번호",
        "type": "string",
        "description": "직원 고유 식별번호",
        "aliases": ["직원번호", "사번", "employee_id", "emp_no", "직원ID"],
        "examples": ["12345", "EMP001", "사원-001"],
        "required": True,
        "sheet": "재직자"
    },
    {
        "field_name": "이름",
        "type": "string",
        "description": "직원 성명",
        "aliases": ["성명", "name", "full_name", "employee_name"],
        "examples": ["홍길동", "김철수", "Hong Gildong"],
        "required": True,
        "sheet": "재직자"
    },
    ...
]
```

**필수 필드** (7개):
1. 사원번호
2. 이름
3. 생년월일
4. 성별
5. 입사일자
6. 종업원구분
7. 기준급여

**선택 필드** (13개):
- 부서, 직급, 전화번호, 이메일, 제도구분
- 퇴직일, 사유, 퇴직금, 당년도퇴직금추계액
- 차년도퇴직금추계액, 사유발생일, 금액, 참고사항

### 진단 질문 (28개)

```python4
ALL_QUESTIONS = 
  DATA_QUALITY_QUESTIONS +      # 14개 (기존)
  FINANCIAL_ASSUMPTIONS +       # 3개 (q15-q17)
  RETIREMENT_SETTINGS +         # 3개 (q18-q20)
  HEADCOUNT_AGGREGATES +        # 5개 (q21-q25)
  AMOUNT_AGGREGATES             # 3개 (q26-q28)
```

**Layer 2 검증용 질문** (8개):
- q21: 임원 인원 (`counts_I26_I39[0]`)
- q22: 직원 인원 (`counts_I26_I39[1]`)
- q23: 계약직 인원 (`counts_I26_I39[2]`)
- q24: 재직자 합계 (`counts_I26_I39[3]`)
- q25: 퇴직자 합계 (`counts_I26_I39[4]`)
- q26: 임원 퇴직금 (`sums_I40_I51[0]`)
- q27: 직원 퇴직금 (`sums_I40_I51[1]`)
- q28: 계약직 퇴직금 (`sums_I40_I51[2]`)

### 검증 결과 구조

```python
{
    "status": "passed" | "warnings" | "failed",
    "total_checks": 8,
    "passed": 5,
    "warnings": [
        {
            "question_id": "q21",
            "severity": "high" | "low" | "info" | "error",
            "message": "...",
            "user_input": "20명",
            "calculated": "17명",
            "diff": 3,
            "diff_percent": 17.6
        }
    ]
}
```

---

## 🤖 AI 헤더 매칭 시스템

### 작동 원리

```python
# 1. 고객 헤더 입력
customer_headers = ["사번", "이름", "출생년월일", "입사날짜"]

# 2. GPT-4o 호출 (Primary)
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "system",
        "content": "당신은 Excel 헤더를 표준 필드에 매칭하는 전문가입니다..."
    }, {
        "role": "user",
        "content": f"다음 헤더를 매칭하세요:\n{customer_headers}\n\n표준 필드:\n{STANDARD_FIELDS}"
    }],
    response_format={"type": "json_object"}
)

# 3. 응답 파싱
{
    "mappings": {
        "사번": {"standard_field": "사원번호", "confidence": 0.95},
        "이름": {"standard_field": "이름", "confidence": 1.0},
        "출생년월일": {"standard_field": "생년월일", "confidence": 0.92}
    },
    "unmapped": [],
    "missing_required": [],
    "total_confidence": 0.96
}
```

### 폴백 모드 (API 없을 때)

```python
from difflib import SequenceMatcher

def _fallback_match(customer_headers, standard_fields):
    mappings = {}
    for customer_header in customer_headers:
        best_match = None
        best_ratio = 0.0
        
        # 정규화
        normalized = re.sub(r'\s+', ' ', customer_header.lower())
        
        # 표준 필드와 모든 alias 비교
        for field in standard_fields:
            for alias in field["aliases"]:
                ratio = SequenceMatcher(None, normalized, alias.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = field["field_name"]
        
        if best_ratio >= 0.7:  # 신뢰도 임계값
            mappings[customer_header] = {
                "standard_field": best_match,
                "confidence": best_ratio
            }
    
    return mappings
```

**정확도**:
- AI (GPT-4o): 95-100%
- Fallback: 71-100% (형식에 따라)

---

## 🔍 Layer 2 검증 알고리즘

### 검증 로직

```python
def validate_chatbot_answers(chatbot_answers, calculated_aggregates, tolerance_percent=5.0):
    warnings = []
    
    for question in get_validation_questions():
        user_value = chatbot_answers.get(question["id"])
        validate_path = question["validate_against"]  # "counts_I26_I39[0]"
        
        # 경로 파싱 → calculated_aggregates에서 값 추출
        calculated_value = _extract_value(calculated_aggregates, validate_path)
        
        # 비교
        if user_value != calculated_value:
            diff = user_value - calculated_value
            diff_percent = abs(diff / calculated_value * 100) if calculated_value != 0 else 100
            
            # 심각도 판단
            if diff_percent > tolerance_percent:
                severity = "high"
            else:
                severity = "low"
            
            warnings.append({
                "question_id": question["id"],
                "severity": severity,
                "message": f"⭕ 명부에서 계산한 값은 {calculated_value}{question['unit']}이지만, 당신은 {user_value}{question['unit']}이라고 입력하셨습니다. (차이: {diff_percent:.1f}%)",
                "user_input": f"{user_value}{question['unit']}",
                "calculated": f"{calculated_value}{question['unit']}",
                "diff": diff,
                "diff_percent": diff_percent
            })
    
    return {
        "status": "failed" if any(w["severity"] == "high" for w in warnings) else "passed",
        "total_checks": len(validation_questions),
        "passed": len(validation_questions) - len(warnings),
        "warnings": warnings
    }
```

### Tolerance 설정

- **5% 이상**: 심각한 불일치 (빨간색)
- **5% 미만**: 경미한 차이 (노란색)
- **0%**: 완벽하게 일치 (경고 없음)

---

## 📊 Excel 경고 시스템

### 셀 스타일 적용

```python
from openpyxl.styles import PatternFill
from openpyxl.comments import Comment

# 심각한 경고 (빨간색)
error_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

# 경미한 경고 (노란색)
warning_fill = PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid")

# 셀 매핑
CELL_MAPPING = {
    "q21": "I14",  # 임원 인원
    "q22": "I15",  # 직원 인원
    "q23": "I16",  # 계약직 인원
    "q26": "I29",  # 퇴직금 합계
    ...
}

# 경고 적용
for warning in validation_warnings:
    cell_address = CELL_MAPPING.get(warning["question_id"])
    cell = ws[cell_address]
    
    # 배경색
    if warning["severity"] == "high":
        cell.fill = error_fill
    else:
        cell.fill = warning_fill
    
    # 코멘트
    cell.comment = Comment(warning["message"], "WIKISOFT2")
```

---

## 🛡️ 에러 처리

### 파싱 경고 시스템

**stdout 캡처**:
```python
import sys
from io import StringIO

# stdout 리다이렉트
captured_output = StringIO()
old_stdout = sys.stdout
sys.stdout = captured_output

try:
    calculated = aggregate_from_excel(content)
finally:
    sys.stdout = old_stdout

# 경고 추출
parsing_warnings = []
for line in captured_output.getvalue().split('\n'):
    if line.startswith('❌'):
        parsing_warnings.append({"severity": "error", "message": line[2:].strip()})
    elif line.startswith('⚠️'):
        parsing_warnings.append({"severity": "warning", "message": line[2:].strip()})
```

**경고 유형**:
1. **API 키 없음**: "OpenAI API 키 없음. 폴백 사용 (정확도 낮음)"
2. **매칭 실패**: "[재직자] AI 매칭 실패. 폴백 사용 중"
3. **필수 필드 누락**: "필수 필드 누락: ['이름', '종업원구분']"
4. **낮은 신뢰도**: "낮은 신뢰도 매칭 (0.65): '직원타입' → '종업원구분'"

---

## 🧪 테스트

### test_layer2_integration.py

```python
# 전체 워크플로우 테스트
def test_full_workflow():
    # 1. 명부 파일 파싱
    with open('roster.xls', 'rb') as f:
        roster_content = f.read()
    
    # 2. 자동 집계 계산
    calculated = aggregate_from_excel(roster_content)
    
    # 3. 챗봇 답변 시뮬레이션 (의도적 오류 포함)
    chatbot_answers = {
        "q21": 20,  # 실제는 17 → 17.6% 차이
        "q22": 664,
        "q26": 7000000000  # 실제는 6789774140 → 3.1% 차이
    }
    
    # 4. Layer 2 검증
    validation_result = validate_chatbot_answers(
        chatbot_answers, 
        calculated, 
        tolerance_percent=5.0
    )
    
    # 5. Excel 생성
    excel_bytes = save_sheet_1_2_from_chatbot_to_bytes(
        chatbot_answers,
        validation_result["warnings"],
        company_info,
        "20251225"
    )
    
    # 검증
    assert validation_result["status"] == "failed"
    assert len(validation_result["warnings"]) == 3
    assert excel_bytes is not None
```

**예상 결과**:
```
✅ 통합 테스트 완료
검증 상태: FAILED
⚠️  심각한 불일치가 발견되었습니다. Excel 파일을 확인하세요.

생성된 파일: test_layer2_validation.xlsx
빨간 배경 셀 = 심각한 불일치, 노란 배경 셀 = 경미한 차이
```

### test_ai_header_matching.py

```python
# 5가지 헤더 형식 테스트
def test_various_header_formats():
    test_cases = [
        {
            "name": "표준 한글",
            "headers": ["사원번호", "이름", "생년월일"],
            "expected_rate": 1.0  # 100%
        },
        {
            "name": "영어",
            "headers": ["EmpNo", "FullName", "DOB"],
            "expected_rate": 1.0
        },
        {
            "name": "혼합 + 줄바꿈",
            "headers": ["사원\nID", "성명", "Birth\nDate"],
            "expected_rate": 0.86  # 86%
        },
        {
            "name": "비표준 한글",
            "headers": ["직원넘버", "태어난날", "입사했어요"],
            "expected_rate": 0.71  # 71%
        }
    ]
    
    for case in test_cases:
        result = ai_match_columns(case["headers"])
        match_rate = len(result["mappings"]) / len(case["headers"])
        assert match_rate >= case["expected_rate"]
```

---

## 📦 배포 체크리스트

### 프로덕션 준비

- [ ] OPENAI_API_KEY 환경변수 설정
- [ ] HTTPS 인증서 발급 (SSL_CERTFILE, SSL_KEYFILE)
- [ ] API_TOKEN 설정 (엔드포인트 보호)
- [ ] CORS_ORIGINS 화이트리스트 설정
- [ ] 세션 TTL/MAX_SESSIONS 튜닝
- [ ] 로그 레벨 설정 (INFO/WARNING)
- [ ] 파일 업로드 크기 제한 확인 (50MB)

### 모니터링

```python
# 로깅 예시
logger.info(f"Session created: {session_id}")
logger.warning(f"Fallback matching used: {sheet_type}")
logger.error(f"Validation failed: {validation_result}")
```

### 성능 최적화

- 세션 메모리: LRU 캐시로 오래된 세션 자동 삭제
- 파일 크기: 50MB 제한, 50,000행 제한
- API 호출: GPT-4o 속도 3-5초, 폴백 즉시

---

## 🔄 버전 히스토리

### v2.1 (2025-12-26) - Phase 2.1 완료
- 자연스러운 유사도 기반 헤더 매칭을 기본값으로 확정 (강제 키워드 매핑 제거)
- 24개 진단 질문 체계 확정: 퇴직자 총합 자동 계산으로 질문 축소 및 UX 개선
- 뒤로가기 및 버튼 위치 고정 등 프론트엔드 UX 개선
- `.env` 로드 및 `OPENAI_API_KEY` 설정 반영 (AI 모드 활성화 시 95%+ 정확도)
- `xlrd` 추가로 .xls 지원, OpenAI 라이브러리 업그레이드
- 필수 필드 누락·신뢰도 경고 정책 정비 (과도한 에러 → 정보/경고 중심)
- 문서 일괄 업데이트 (README/OVERVIEW/REBUILD_GUIDE)

### v2.0 (2025-12-25) - Phase 2 완료
- ✅ AI 헤더 매칭 시스템 (column_matcher.py)
- ✅ 표준 스키마 정의 (standard_schema.py, 20개 필드)
- ✅ Layer 2 검증 (validation_layer2.py, 8개 체크)
- ✅ 24개 진단 질문 (diagnostic_questions.py) - 자동 계산 포함
- ✅ Excel 경고 시스템 (sheet_generator.py, 빨강/노랑 셀)
- ✅ 폴백 에러 처리 (parsing_warnings, used_ai 플래그)
- ✅ 하드코딩 제거 (HEADER_MAP 삭제)
- ✅ 통합 테스트 3종 (layer2, ai_matching, api_warnings)

### v1.0 (2025-12-24) - Phase 1 완료
- ✅ FastAPI 기본 서버
- ✅ 파일 업로드/파싱
- ✅ Layer 1 검증 (코드 룰)
- ✅ 이상치 탐지
- ✅ 세션 관리

---

**문의**: 프로젝트 관리자
