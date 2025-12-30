# 🚀 WIKISOFT2 - HR 명부 자동 검증 시스템

**Phase 2.1 완료** | **2025-12-26**

AI 기반 Excel 헤더 매칭 + 교차 검증 + 시각적 경고 시스템

---

## 📋 목차

- [빠른 시작](#-빠른-시작)
- [주요 기능](#-주요-기능)
- [문서](#-문서)
- [프로젝트 구조](#-프로젝트-구조)
- [테스트](#-테스트)
- [API](#-api)

---

## 🎯 개요

**WIKISOFT2**는 HR 담당자가 고객사로부터 받은 직원 명부를 자동으로 검증하고, AI로 헤더를 매칭하며, Excel에 경고를 시각화하는 시스템입니다.

### 핵심 가치

| 기능 | 설명 | 효과 |
|------|------|------|
| **자연스러운 헤더 매칭** | 고객사별 다른 Excel 헤더 유사도 기반 인식 | 하드코딩 제거, 무제한 확장 |
| **교차 검증** | 챗봇 답변 vs 명부 계산값 비교 | 정확도 70% (폴백) / 95%+ (AI) |
| **시각적 경고** | Excel 셀 강조 (빨강/노랑) | 직관적 피드백 |
| **자동 계산** | 퇴직자 총합 자동 계산 | 질문 제거, UX 개선 |

---

## ⚡ 빠른 시작

### 1. 설치

```bash
# 클론
cd /Users/kj/Desktop/wiki/WIKISOFT2

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (선택)
export OPENAI_API_KEY="sk-..."  # 프로덕션에서 필수
```

### 2. 실행

```bash
# 서버 시작
python -m uvicorn external.api.main:app --reload --port 8000

# 브라우저에서 확인
open http://localhost:8000/docs
```

안정 실행 스니펫(포트 정리 후 백그라운드 실행):

```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
/Users/kj/Desktop/wiki/.venv/bin/python -m uvicorn external.api.main:app --reload --port 8000 2>&1 &
```

### 3. 테스트

```bash
# 전체 워크플로우 테스트
python test_layer2_integration.py

# AI 헤더 매칭 테스트
python test_ai_header_matching.py

# API 경고 시스템 테스트
python test_api_warnings.py
```

---

## ✨ 주요 기능

### 1️⃣ AI 헤더 매칭

**문제**: 고객사마다 다른 Excel 헤더
- 세라젬: "사원번호", "성명", "생년월일"
- A회사: "직원ID", "이름", "출생일"
- B회사: "EmpNo", "Name", "DOB"

**솔루션**: GPT-4o가 자동으로 표준 필드에 매칭
```python
customer_headers = ["직원ID", "이름", "출생일"]
↓ AI 매칭
standard_fields = ["사원번호", "이름", "생년월일"]
```

**정확도**:
- AI (GPT-4o): 95-100%
- 폴백 (문자열): 71-100%

### 2️⃣ Layer 2 교차 검증

**원리**: 챗봇 답변과 명부 계산값 비교

**예시**:
```
챗봇: "임원이 20명입니다"
명부: 17명 (종업원구분=3 카운트)
결과: ❌ 차이 17.6% → 빨간 경고
```

**검증 항목**: 8개 (인원 5개 + 금액 3개)

### 3️⃣ Excel 경고 시스템

**시각화**:
- 🔴 빨간 배경: 차이 5% 이상
- 🟡 노란 배경: 차이 5% 미만
- 💬 셀 코멘트: 마우스 오버 시 상세 메시지

![Excel 예시](https://via.placeholder.com/600x200?text=Excel+Warning+Example)

---

## 📚 문서

| 문서 | 대상 | 설명 |
|------|------|------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | 비기술진 | 프로젝트 개요, 아키텍처, 성능 지표 |
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | 개발자 | API 명세, 데이터 모델, 알고리즘 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 전체 | 레이어/데이터 흐름/운영 모드 요약 |
| [REBUILD_GUIDE.md](REBUILD_GUIDE.md) | 신규 개발자 | 설치, 실행, 컴포넌트 가이드 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여자 | 코딩 규칙, 브랜치/PR 체크리스트, PII 지침 |
| [CHANGELOG.md](CHANGELOG.md) | 모두 | 버전별 변경 이력 (v2.1 포함) |
| [PRIVACY_GUIDE.md](PRIVACY_GUIDE.md) | 보안/운영 | 프라이버시 원칙, Do/Don't, 마스킹 유틸 |
| [PHASE3_PLAN.md](PHASE3_PLAN.md) | 기획/개발 | v3 간단 계획, Quick Wins, 로드맵 |

---

## 📂 프로젝트 구조

```
WIKISOFT2/
├── external/api/
│   └── main.py                    # FastAPI 서버 (879줄)
├── internal/
│   ├── parsers/
│   │   ├── standard_schema.py     # ⭐ 20개 표준 필드
│   │   └── ceragem_parser.py      # Excel 파싱 + AI 매칭
│   ├── ai/
│   │   ├── column_matcher.py      # ⭐ AI 헤더 매칭
│   │   └── diagnostic_questions.py # ⭐ 24개 질문
│   ├── processors/
│   │   └── validation_layer2.py   # ⭐ 교차 검증
│   └── generators/
│       └── sheet_generator.py     # ⭐ Excel 경고 출력
└── tests/
    ├── test_layer2_integration.py  # 통합 테스트
    ├── test_ai_header_matching.py  # AI 매칭 테스트
    └── test_api_warnings.py        # 경고 시스템 테스트

⭐ = Phase 2 신규/대폭 수정
```

---

## 🧪 테스트

### 통합 테스트
```bash
python test_layer2_integration.py
```

**결과**:
```
✅ 통합 테스트 완료
검증 상태: FAILED (3개 경고)
- q21 (임원): 20 vs 17 (차이 17.6%) 🔴
- q24 (재직자): 480 vs 477 (차이 0.6%) 🟡
생성된 파일: test_layer2_validation.xlsx
```

### AI 매칭 테스트
```bash
python test_ai_header_matching.py
```

**결과**:
```
✅ Test 1 (표준 한글): 7/7 (100%)
✅ Test 2 (영어): 7/7 (100%)
✅ Test 3 (혼합): 6/7 (86%)
⚠️  Test 4 (비표준): 5/7 (71%)
```

---

## 🔌 API

### 엔드포인트

```http
GET  /diagnostic-questions        # 24개 질문 조회
POST /validate-with-roster        # Layer 2 검증 실행
POST /generate-with-validation    # Excel 다운로드
```

### 예시: Layer 2 검증

**요청**:
```bash
curl -X POST http://localhost:8000/validate-with-roster \
  -F "file=@roster.xlsx" \
  -F 'chatbot_answers={"q21": 20, "q22": 664}'
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
        "message": "⭕ 명부에서 계산한 값은 17명이지만...",
        "diff_percent": 17.6
      }
    ]
  },
  "parsing_warnings": [
    {
      "severity": "warning",
      "message": "[재직자] 폴백 매칭 사용됨"
    }
  ],
  "session_id": "abc123"
}
```

**Swagger UI**: http://localhost:8000/docs

---

## 🔧 기술 스택

- **Backend**: Python 3.12+, FastAPI
- **AI**: OpenAI GPT-4o
- **Excel**: openpyxl, pandas, xlrd
- **검증**: SequenceMatcher (폴백), NumPy

---

## 🚀 로드맵

### ✅ Phase 1 (완료)
- FastAPI 서버, Layer 1 검증, 이상치 탐지

### ✅ Phase 2 (완료)
- AI 헤더 매칭, Layer 2 검증, Excel 경고, 폴백 에러 처리

### 📋 Phase 3 (예정)
- React + TypeScript 프론트엔드
- 챗봇 인터페이스
- 통계 대시보드

---

## 📊 성과

| 지표 | Phase 1 | Phase 2 | 개선 |
|------|---------|---------|------|
| 헤더 지원 | 세라젬만 | 무제한 | ∞ |
| 검증 정확도 | 없음 | 8개 체크 | ∞ |
| 처리 시간 | 30분 | 1분 | 30x |

---

## 📞 문의

**프로젝트**: WIKISOFT2  
**Phase**: 2.1 완료 (2025-12-26)  
**문의**: 프로젝트 관리자

---

**© 2025 WIKISOFT - 사내 사용 전용**

---

## 🧭 프로젝트 특성 (핵심 정리)

- 자연스러운 헤더 매칭: 문자열 유사도 기반(SequenceMatcher) + 정규화로 고객 헤더를 표준 스키마에 자연스럽게 매핑
- AI 선택형 모드: `OPENAI_API_KEY` 설정 시 GPT-4o로 95%+ 정확도, 기본 폴백은 70%±
- 불필요 질문 제거: 퇴직자 총합은 자동 계산(q24+q25+q26), 전체 24개 질문 체계 유지
- 시각적 경고: Excel 셀 강조(빨강/노랑)로 수정 포인트를 직관적으로 제시
- 일관된 UX: 뒤로가기, 버튼 위치 고정(그리드 + min-height), 긴 문구에도 안정적 배치

## ⚙️ 운영 모드와 정확도

- 폴백 모드(기본): 오프라인·내부망에서도 동작, 문자열 유사도 기반으로 약 70% 정확도
- AI 모드(선택): 헤더 메타데이터 중심 비교 권장, 민감정보 전송 금지 가이드 포함
- 경고 정책: 필수 필드 누락, 낮은 신뢰도, 매칭 실패 비율 과다 시 경고 노출

## 🔒 데이터 처리와 보안

- 기본 폴백: 외부 전송 없음(로컬 처리)
- AI 사용: 헤더 중심 비교, 마스킹 유틸로 PII 사전 제거 가능

## 🧩 헤더 매칭 설계 요약

- 정규화: 개행·괄호 제거, 공백 축약, 소문자화
- 유사도: 표준 필드/별칭과 SequenceMatcher로 점수 산출
- 임계값·경고: 임계값 미만은 `unmapped`, 필수 누락·신뢰도 낮음·매칭 실패 비율 과다 시 경고
- AI 모드: 프롬프트 기반 매핑과 근거(reason) 포함 응답

## 🗂️ 진단 질문 체계(총 24개)

- 기본 데이터 품질(14)
- 인원 집계(6): 재직/퇴직 유형별 수량, 퇴직자 총합 자동 계산
- 금액 집계(4): 퇴직급여 관련 금액 항목의 합계/전환/기타 반환

## 🚧 한계와 향후 계획

- 폴백 정확도 한계: 복합 헤더에서 경고 증가 가능
- 시트 의존성: 필수 시트/필드 누락 시 경고·오류 처리
- 향후: 수동 매핑 UI, 신뢰도 대시보드, 별칭 사전 확장

---

## 🧠 Agent Framework & 배치 처리 (Phase 2.2)

### 구성 요소
- **ReACT Loop**: 사고→행동→관찰 반복으로 자동 검증 수행. 내부 에이전트는 11개 도구를 사용.
- **Tool Registry (11개 도구)**: 파싱/정규화/스키마검증/교차검증/통계/이상치/분포분석/오타수정/숫자정규화/불일치해결 포함.
- **Confidence Calculator**: 4요소(도구선택/도구실행/데이터품질/결과신뢰도)로 종합 신뢰도 산출.
- **Decision Engine**: 정책 준수·데이터 품질 점검을 기반으로 최종 권장(자동완료/사람확인) 결정.
- **Memory System**: 패턴/오류/규칙을 저장·검색·통계·내보내기/임포트 지원(인메모리, 1000개 LRU).

### API 사용 예시
- 단일 자동 검증:
```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \
  -F "file=@path/to.xlsx" \
  http://localhost:8000/auto-validate
```

- 배치 자동 검증(최대 10개):
```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \
  -F "files=@file1.xlsx" -F "files=@file2.xlsx" \
  http://localhost:8000/batch-validate
```

### CLI(터미널) 실행
에이전트 검증 CLI로 파일을 바로 검증할 수 있습니다.
```bash
python -m internal.tools.run_agent_validate --file path/to.xlsx --steps 3 --threshold 0.7
```

---

## ⚙️ 설정 매니저 (하드코딩 유지 + 외부 병합)

### 스키마 (20개 표준 필드 고정)
- 파일: `internal/config/schema_config.py`
- 기본은 하드코딩된 20개 필드를 사용합니다(고객 자료는 AI 매핑으로 표준 스키마에 맞춥니다).
- 필요 시 외부 JSON/YAML로 필드를 병합(덮어쓰기)할 수 있으나, 호출하지 않으면 기본 하드코딩 상태를 그대로 사용합니다.

예시:
```python
from internal.config.schema_config import SchemaConfig
s = SchemaConfig()
s.load_from_file("schema_override.json")  # 존재하지 않으면 False, 기본 유지
```

### 프롬프트 설정
- 파일: `internal/config/prompt_config.py`
- 기본 프롬프트는 하드코딩되어 있으며, 외부 JSON/YAML로 병합만 수행합니다.
```python
from internal.config.prompt_config import PromptConfig
p = PromptConfig()
p.load_from_file("prompts.yaml")  # 병합. 미호출 시 변경 없음
```

---

## 🧭 Phase 2 마이그레이션 가이드
Phase 3(자율화)로 가기 전, 메모리/검색/오케스트레이션을 확장하는 가이드입니다.

- 문서: [PHASE2_MIGRATION_GUIDE.md](PHASE2_MIGRATION_GUIDE.md)
- 주요 내용:
  - In-memory → Redis 메모리로 이관(환경변수 스위치)
  - Chroma Vector DB로 패턴 임베딩·유사 검색
  - LangChain/LlamaIndex로 에이전트 오케스트레이션 표준화
