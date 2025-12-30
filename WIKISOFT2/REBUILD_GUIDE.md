# 🔄 WIKISOFT2 개발 가이드

**최종 업데이트**: 2025-12-26  
**Phase 2.1 완료** - 프로덕션 준비 완료

---

## 🚀 빠른 시작 (5분)

### 1. 환경 설정

```bash
# 레포지토리 클론 (실제 경로로 대체)
cd /Users/kj/Desktop/wiki/WIKISOFT2

# Python 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성 (WIKISOFT2 디렉토리)
OPENAI_API_KEY="sk-proj-..."
MAX_SESSIONS=50
SESSION_TIMEOUT_MINUTES=60
```

**참고**:
- OpenAI API 키는 선택사항 (없으면 폴백 모드)
- 폴백 모드: 자연스러운 유사도 기반 매칭 (정확도 70%)
- API 키 있음: GPT-4o 매칭 (정확도 95%+)

### 3. 서버 실행

```bash
# 개발 모드 (자동 reload)
python -m uvicorn external.api.main:app --reload --port 8000

# 프로덕션 모드
uvicorn external.api.main:app --host 0.0.0.0 --port 8000
```

### 4. 테스트

```bash
# Layer 2 통합 테스트
python test_layer2_integration.py

# AI 헤더 매칭 테스트
python test_ai_header_matching.py

# API 경고 시스템 테스트
python test_api_warnings.py
```

**서버 실행 확인**: http://localhost:8000/docs (Swagger UI)

---

## 📂 프로젝트 구조

```
WIKISOFT2/
├── external/api/
│   └── main.py                    # FastAPI 서버 (879줄)
│       ├── GET  /diagnostic-questions
│       ├── POST /validate-with-roster
│       └── POST /generate-with-validation
│
├── internal/
│   ├── models/
│   │   └── session.py             # 세션 클래스 (120분 TTL)
│   │
│   ├── parsers/
│   │   ├── standard_schema.py     # ⭐ 20개 표준 필드 정의
│   │   └── ceragem_parser.py      # Excel 파싱 + AI 매칭
│   │
│   ├── ai/
│   │   ├── column_matcher.py      # ⭐ AI 헤더 매칭 (GPT-4o + 폴백)
│   │   ├── diagnostic_questions.py # ⭐ 28개 진단 질문
│   │   ├── prompts.py             # GPT 프롬프트 템플릿
│   │   └── question_builder.py    # 챗봇 질문 생성
│   │
│   ├── processors/
│   │   ├── validation_layer1.py   # 코드 룰 검증
│   │   └── validation_layer2.py   # ⭐ 교차 검증 (챗봇 vs 명부)
│   │
│   ├── generators/
│   │   ├── aggregate_calculator.py # 인원/금액 자동 계산
│   │   └── sheet_generator.py     # ⭐ Excel 출력 + 경고 셀
│   │
│   ├── validation/
│   │   └── anomaly_detector.py    # 이상치 탐지 (통계 기반)
│   │
│   └── utils/
│       ├── date_utils.py          # 날짜 정규화
│       ├── masking.py             # 개인정보 마스킹
│       └── logging.py             # 로깅 유틸
│
├── tests/
│   ├── test_layer2_integration.py  # ⭐ 전체 워크플로우 테스트
│   ├── test_ai_header_matching.py  # ⭐ AI 매칭 5가지 시나리오
│   └── test_api_warnings.py        # ⭐ stdout 캡처 테스트
│
├── requirements.txt               # 의존성 목록
├── PROJECT_OVERVIEW.md            # 프로젝트 개요 (비기술)
├── PROJECT_SPEC.md                # 기술 명세서 (이 문서)
└── REBUILD_GUIDE.md               # 개발 가이드 (현재 문서)

⭐ = Phase 2에서 추가/대폭 수정
```

---

## 🔧 핵심 컴포넌트 가이드

### 1. AI 헤더 매칭 (column_matcher.py)

**목적**: 고객사별 다른 Excel 헤더를 표준 필드에 자동 매핑

**사용법**:
```python
from internal.ai.column_matcher import ai_match_columns

customer_headers = ["사번", "성명", "출생년월일", "입사날짜"]

result = ai_match_columns(
    customer_headers, 
    sheet_type="재직자",
    api_key=os.getenv("OPENAI_API_KEY"),
    confidence_threshold=0.7
)

print(result)
# {
#   "mappings": {
#     "사번": {"standard_field": "사원번호", "confidence": 0.95},
#     "성명": {"standard_field": "이름", "confidence": 1.0},
#     ...
#   },
#   "unmapped": [],
#   "missing_required": [],
#   "total_confidence": 0.96,
#   "warnings": [],
#   "used_ai": True
# }
```

**Primary vs Fallback**:
- **API 키 있음**: GPT-4o 사용 (95-100% 정확도)
- **API 키 없음**: 문자열 유사도 (71-100% 정확도) + 경고

**경고 유형**:
```python
{
  "warnings": [
    {
      "severity": "error",
      "message": "AI 매칭 실패. 폴백 사용 중",
      "details": {"used_ai": False}
    },
    {
      "severity": "warning",
      "message": "필수 필드 누락: ['이름', '종업원구분']"
    }
  ]
}
```

### 2. 표준 스키마 (standard_schema.py)

**목적**: 모든 고객 파일을 통일된 20개 필드로 변환

**주요 필드**:
```python
STANDARD_SCHEMA = [
    {
        "field_name": "사원번호",
        "type": "string",
        "description": "직원 고유 식별번호",
        "aliases": ["직원번호", "사번", "employee_id", "emp_no", "직원ID", "EmpNo"],
        "examples": ["12345", "EMP001"],
        "required": True,
        "sheet": "재직자"
    },
    {
        "field_name": "이름",
        "aliases": ["성명", "name", "full_name", "employee_name"],
        ...
    },
    ...
]
```

**헬퍼 함수**:
```python
from internal.parsers.standard_schema import get_required_fields, find_field_by_alias

# 필수 필드만 조회
required = get_required_fields("재직자")
# ['사원번호', '이름', '생년월일', '성별', '입사일자', '종업원구분', '기준급여']

# alias로 표준 필드 찾기
field = find_field_by_alias("직원ID")
# '사원번호'
```

### 3. Layer 2 검증 (validation_layer2.py)

**목적**: 챗봇 답변과 명부 계산값 교차 검증

**사용법**:
```python
from internal.processors.validation_layer2 import validate_chatbot_answers

# 챗봇 답변
chatbot_answers = {
    "q21": 20,  # 임원 인원
    "q22": 664, # 직원 인원
    "q26": 7000000000  # 퇴직금
}

# 명부에서 계산한 값
calculated_aggregates = {
    "counts_I26_I39": [17.0, 664.0, 69.0, ...],
    "sums_I40_I51": [6789774140.0, ...]
}

# 검증 실행
result = validate_chatbot_answers(
    chatbot_answers, 
    calculated_aggregates, 
    tolerance_percent=5.0
)

print(result)
# {
#   "status": "failed",
#   "total_checks": 8,
#   "passed": 5,
#   "warnings": [
#     {
#       "question_id": "q21",
#       "severity": "high",  # 차이 17.6% > 5%
#       "message": "⭕ 명부에서 계산한 값은 17명이지만...",
#       "user_input": "20명",
#       "calculated": "17명",
#       "diff": 3,
#       "diff_percent": 17.6
#     }
#   ]
# }
```

**Tolerance 규칙**:
- `diff_percent > 5%` → `severity: "high"` (빨간색)
- `diff_percent <= 5%` → `severity: "low"` (노란색)
- `diff_percent == 0%` → 경고 없음

### 4. Excel 경고 시스템 (sheet_generator.py)

**목적**: (1-2) 시트에 검증 경고를 시각화

**사용법**:
```python
from internal.generators.sheet_generator import save_sheet_1_2_from_chatbot_to_bytes

excel_bytes = save_sheet_1_2_from_chatbot_to_bytes(
    chatbot_answers={
        "q15": 3.5,  # 할인율
        "q21": 20,   # 임원 인원
        ...
    },
    validation_warnings=[
        {
            "question_id": "q21",
            "severity": "high",
            "message": "⭕ 명부에서 계산한 값은 17명이지만..."
        }
    ],
    company_info={
        "name": "세라젬",
        "phone": "02-1234-5678",
        "email": "hr@example.com"
    },
    작성기준일="20251225"
)

# BytesIO 또는 파일로 저장
with open("output.xlsx", "wb") as f:
    f.write(excel_bytes.getvalue())
```

**결과물**:
- 셀 I14 (임원 인원): 🔴 빨간 배경 + 💬 코멘트
- 셀 I29 (퇴직금): 🟡 노란 배경 + 💬 코멘트

---

## 🧪 테스트 가이드

### test_layer2_integration.py

**목적**: 전체 워크플로우 E2E 테스트

**시나리오**:
1. 세라젬 명부 파일 파싱
2. 인원/금액 자동 계산
3. 챗봇 답변 시뮬레이션 (의도적 오류 포함)
4. Layer 2 검증 실행
5. Excel 파일 생성 (경고 포함)
6. 셀 스타일/코멘트 확인

**실행**:
```bash
python test_layer2_integration.py
```

**예상 출력**:
```
======================================================================
Layer 2 검증 시스템 통합 테스트
======================================================================

[1단계] 명부 파일 파싱...
⚠️  [재직자] 폴백 매칭 사용됨 - OpenAI API 키 설정 권장

[2단계] 명부에서 자동 집계 계산...
✅ counts_I26_I39: [17.0, 664.0, 69.0, ...]

[3단계] 챗봇 답변 시뮬레이션...
✅ 8개 질문 답변 완료

[4단계] Layer 2 검증 실행...
⚠️  검증 실패: 3개 경고 발견
  - q21 (임원): 20 vs 17 (차이 17.6%) 🔴
  - q24 (재직자): 480 vs 477 (차이 0.6%) 🟡

[5단계] Excel 파일 생성...
✅ 파일 크기: 5,940 bytes

[6단계] 셀 검증...
  I14 (임원): 빨간 배경 ✅
  I14 코멘트: "⭕ 명부에서 계산한 값은..." ✅

======================================================================
✅ 통합 테스트 완료
======================================================================
```

### test_ai_header_matching.py

**목적**: AI 매칭 정확도 테스트 (5가지 시나리오)

**테스트 케이스**:
1. **표준 한글**: ["사원번호", "이름", "생년월일"] → 100%
2. **비표준 한글**: ["직원넘버", "태어난날"] → 71%
3. **영어**: ["EmpNo", "FullName", "DOB"] → 100%
4. **혼합**: ["사원ID", "Name", "출생일"] → 86%
5. **줄바꿈**: ["사원번호\n(Employee ID)"] → 86%

**실행**:
```bash
python test_ai_header_matching.py
```

**예상 출력**:
```
✅ Test 1 (표준 한글): 7/7 (100%) ✅ 통과
✅ Test 2 (비표준 한글): 5/7 (71%) ⚠️  낮음
✅ Test 3 (영어): 7/7 (100%) ✅ 통과
✅ Test 4 (혼합): 6/7 (86%) ✅ 통과
✅ Test 5 (줄바꿈): 6/7 (86%) ✅ 통과

폴백 모드 테스트:
✅ 7/7 (100%) - 영어 헤더는 폴백도 완벽
```

### test_api_warnings.py

**목적**: stdout 캡처로 파싱 경고 수집 테스트

**검증 항목**:
- stdout → StringIO 리다이렉트
- ❌/⚠️ 마커 기반 경고 추출
- API 응답에 `parsing_warnings` 포함

**실행**:
```bash
python test_api_warnings.py
```

**예상 출력**:
```
[캡처된 출력 (943 bytes)]
⚠️  OpenAI API 키 없음. 폴백 매칭 사용
❌ [재직자] AI 매칭 실패. 폴백 사용 중
⚠️  [재직자] 매칭 안 된 컬럼: ['참고사항']

[추출된 경고 12개]
1. ⚠️ [warning] OpenAI API 키 없음...
2. ❌ [error] [재직자] AI 매칭 실패...

[API 응답 형식]
{
  "parsing_warnings": [
    {"severity": "warning", "message": "..."},
    {"severity": "error", "message": "..."}
  ],
  "used_ai": false
}
```

---

## 🔌 API 사용 예시

### 1. 진단 질문 조회

```bash
curl http://localhost:8000/diagnostic-questions
```

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
    "total": 28,
    "categories": {
      "data_quality": 14,
      "financial_assumptions": 3,
      "headcount_aggregates": 5,
      "amount_aggregates": 3
    }
  }
}
```

### 2. Layer 2 검증 실행

```bash
curl -X POST http://localhost:8000/validate-with-roster \
  -F "file=@roster.xlsx" \
  -F 'chatbot_answers={"q21": 20, "q22": 664, "q26": 7000000000}'
```

**응답**:
```json
{
  "validation": {
    "status": "failed",
    "total_checks": 8,
    "passed": 5,
    "warnings": [...]
  },
  "calculated_aggregates": {...},
  "parsing_warnings": [
    {
      "severity": "warning",
      "message": "[재직자] 폴백 매칭 사용됨"
    }
  ],
  "session_id": "abc123",
  "message": "검증 완료"
}
```

### 3. Excel 파일 다운로드

```bash
curl -X POST http://localhost:8000/generate-with-validation \
  -d "session_id=abc123" \
  -d "company_name=세라젬" \
  -d "작성기준일=20251225" \
  -o output.xlsx
```

**결과**: 경고 셀이 강조된 Excel 파일 다운로드

---

## 🐛 트러블슈팅

### 문제 1: "OpenAI API 키 없음" 경고

**원인**: OPENAI_API_KEY 환경변수 미설정

**해결**:
```bash
export OPENAI_API_KEY="sk-..."
python -m uvicorn external.api.main:app --reload
```

**임시 해결** (폴백 모드):
- 폴백 모드로 작동 (71-100% 정확도)
- 프로덕션에서는 비권장

### 문제 2: "필수 필드 누락" 에러

**원인**: 고객 파일에 필수 필드가 없음

**필수 필드** (7개):
- 사원번호, 이름, 생년월일, 성별, 입사일자, 종업원구분, 기준급여

**해결**:
1. 고객에게 필수 필드 추가 요청
2. 또는 수동 매핑 UI 구현 (Phase 3)

### 문제 3: "차이 17.6%" 검증 실패

**원인**: 챗봇 답변과 명부 계산값 불일치

**확인 사항**:
1. 명부 파일 종업원구분 컬럼 확인
2. 사용자가 입력한 값 재확인
3. Excel 파일에서 빨간 셀 확인

**해결**:
- 사용자에게 재입력 요청
- 또는 명부 파일 수정

### 문제 4: Import 에러

**증상**:
```
ModuleNotFoundError: No module named 'internal'
```

**해결**:
```bash
# 프로젝트 루트에서 실행
cd /Users/kj/Desktop/wiki/WIKISOFT2
python -m uvicorn external.api.main:app --reload
```

---

## 🚢 프로덕션 배포

### Docker 컨테이너화 (예정)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
ENV USE_HTTPS=true

CMD ["uvicorn", "external.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 환경 변수 체크리스트

```bash
# 필수
export OPENAI_API_KEY="sk-..."

# 보안
export API_TOKEN="your-secret-token"
export USE_HTTPS=true
export SSL_CERTFILE="/path/to/cert.pem"
export SSL_KEYFILE="/path/to/key.pem"

# 성능
export SESSION_TTL_MINUTES=120
export MAX_SESSIONS=100

# CORS
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

### 모니터링

```python
# internal/utils/logging.py 설정
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wikisoft2.log'),
        logging.StreamHandler()
    ]
)
```

**로그 확인**:
```bash
tail -f wikisoft2.log
```

---

## 📚 추가 리소스

### 관련 문서
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 프로젝트 개요
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - 기술 명세서
- [FALLBACK_ERROR_HANDLING_REPORT.md](FALLBACK_ERROR_HANDLING_REPORT.md) - 폴백 에러 처리

### 외부 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [OpenAI API 가이드](https://platform.openai.com/docs)
- [openpyxl 문서](https://openpyxl.readthedocs.io/)

### 커뮤니티
- 프로젝트 관리자에게 문의
- 내부 Slack 채널: #wikisoft2

---

## 🎓 학습 경로

### 초급 (1-2시간)
1. 프로젝트 개요 읽기 (PROJECT_OVERVIEW.md)
2. 빠른 시작 따라하기 (이 문서)
3. test_layer2_integration.py 실행

### 중급 (3-5시간)
1. PROJECT_SPEC.md 읽기
2. column_matcher.py 코드 분석
3. validation_layer2.py 로직 이해
4. 커스텀 테스트 작성

### 고급 (5-10시간)
1. 새로운 진단 질문 추가 (diagnostic_questions.py)
2. 커스텀 필드 추가 (standard_schema.py)
3. Excel 템플릿 수정 (sheet_generator.py)
4. 프론트엔드 통합 (Phase 3)

---

**문의**: 프로젝트 관리자  
**최종 업데이트**: 2025-12-26
