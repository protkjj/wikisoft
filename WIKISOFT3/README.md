# WIKISOFT3

**HR/재무 엑셀 자동 검증 시스템 v3 (완결)**

> 퇴직급여채무 평가를 위한 재직자 명부 자동 검증 AI Agent

---

## Project Status: COMPLETE

WIKISOFT3는 2025.12 ~ 2026.01 개발 기간을 거쳐 **완성된 프로젝트**입니다.
핵심 기능이 모두 구현되어 프로덕션에서 사용 가능하며, 후속 버전인 WIKISOFT 4.1로 보안/개인정보보호 기능이 확장되었습니다.

### 완성도: 95%

| 영역 | 완성도 | 상태 |
|------|--------|------|
| 파싱 | **100%** | ✅ XLS/XLSX, 빈 행 필터, 날짜 변환, 헤더 자동 탐지 |
| 헤더 매칭 | **95%** | ✅ AI + Few-shot + 폴백 |
| 검증 | **95%** | ✅ L1/L2/AI, 중복 탐지, 재검증 |
| 학습 시스템 | **90%** | ✅ 케이스 저장, 자율 학습 |
| 보안 | **90%** | ✅ CORS, Rate Limit, PII 마스킹 |
| UI | **100%** | ✅ SheetEditorPro, AI 사이드바, 다크 모드 |
| 다운로드 | **100%** | ✅ 의심 목록 Excel 다운로드 |

---

## 구현된 기능 상세

### 1. 스마트 Excel 파싱

**파일:** `internal/parsers/parser.py`

| 기능 | 설명 | 구현 방식 |
|------|------|----------|
| 헤더 행 자동 탐지 | A, B, C 대신 실제 헤더 찾기 | 한글 키워드 매칭 (`사원번호`, `성명` 등) |
| 빈 행 자동 제거 | 사원번호 없는 행 필터링 | `dropna(subset=['사원번호'])` |
| 날짜 자동 변환 | Excel 직렬번호 → ISO 날짜 | `36770` → `2000-09-01` |
| 날짜 형식 보존 | 원본 형식 유지 | YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD |
| 시트 자동 선택 | 재직자 명부 시트 우선 | `(2-2) 재직자 명부` 패턴 탐지 |
| 참고사항 필터링 | 불필요한 컬럼 제거 | `참고사항`, `비고` 자동 스킵 |
| 헤더 정규화 | 줄바꿈/공백 제거 | `column.strip().replace('\n', '')` |

```python
# 헤더 탐지 키워드 (parser.py:15-20)
HEADER_KEYWORDS = {
    "사원번호", "직원번호", "사번", "성명", "이름", "생년월일",
    "입사일", "입사일자", "급여", "월급여", "연봉", "직급"
}
```

### 2. AI 헤더 매칭

**파일:** `internal/ai/matcher.py`

| 전략 | 우선순위 | 설명 |
|------|----------|------|
| Few-shot | 1순위 | 학습된 케이스에서 직접 매핑 |
| AI (GPT-4o) | 2순위 | OpenAI API 호출 |
| 규칙 기반 | 3순위 | 유사도 계산 폴백 |

**무시되는 컬럼:**
- `참고사항`, `비고`, `메모`
- `Unnamed` 컬럼
- `구분` (단, `종업원구분`, `제도구분` 등은 매핑됨)

**학습 현황:**
- 40개 케이스 (실제 5개 + 합성 35개)
- 182개 헤더 패턴
- 95% 자동 매핑 정확도

### 3. 3계층 검증 시스템

**Layer 1: 형식 검증** (`validation_layer1.py`)
| 규칙 | 설명 |
|------|------|
| 필수 컬럼 | 사원번호, 성명, 생년월일 존재 확인 |
| 데이터 타입 | 날짜/숫자/문자열 타입 검사 |
| 범위 검사 | 나이 18-100, 급여 > 0 |
| 날짜 유효성 | 미래 날짜, 비현실적 날짜 탐지 |

**Layer 2: 교차 검증** (`validation_layer2.py`)
| 규칙 | 설명 |
|------|------|
| 중복 탐지 | 완전/유사/의심 중복 분류 |
| 논리 일관성 | 입사일 < 생년월일 탐지 |
| 재직 상태 | 퇴사일 있는데 재직 중 표시 |

**Layer 3: AI 검증** (`validation_layer_ai.py`)
| 규칙 | 설명 |
|------|------|
| 컨텍스트 오버라이드 | 임원은 70세 입사 허용 |
| 진단 질문 반영 | 정년, 임금피크제 적용 여부 |
| 학습된 패턴 | 9개 예외 패턴 자동 적용 |

### 4. 자율 학습 시스템

**파일:** `internal/ai/autonomous_learning.py`

```
[행동 기록] → [10개 이벤트마다] → [AI 패턴 분석] → [규칙 자동 생성]
      ↓              ↓                 ↓                ↓
 behavior_logs    자동 트리거      GPT-4o 분석    error_rules.json
```

**학습된 예외 패턴 (9개):**
1. 임원 65세 이상 입사 정상
2. 계약직 저급여 허용 (50만원 이상)
3. 79세 임원/고문 허용
4. 파트타임 근무시간 200시간 미만 정상
5. 연구원 학력 박사 비율 높음
6. 외국인 근로자 비자 만료 전 경고
7. 전환배치 급여 변동 정상
8. 계열사 전출입 경력 인정
9. 임시직 짧은 근속 기간 정상

### 5. SheetEditorPro UI

**파일:** `frontend/src/components/SheetEditorPro.tsx`

| 기능 | 설명 |
|------|------|
| 에러 셀 하이라이트 | 빨간색 테두리 (에러), 주황색 테두리 (경고) |
| AI 사이드바 | 다크 모드 그라데이션, 실시간 AI 대화 |
| 재검증 | 수정 후 해당 셀만 재검증 |
| 형식 자동 유지 | 날짜, 금액 원본 형식 보존 |
| 접기/펼치기 | 컬럼 매핑, 검증 결과 섹션 토글 |

### 6. API 엔드포인트

**핵심 API:**
| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auto-validate` | POST | 파일 업로드 및 자동 검증 |
| `/api/react-agent/validate` | POST | ReACT Agent 기반 검증 |
| `/api/agent/ask` | POST | AI 챗봇 대화 |
| `/api/diagnostic-questions` | GET | 진단 질문 목록 |
| `/api/export/errors` | POST | 의심 목록 Excel 다운로드 |

**학습 API:**
| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/learn/correction` | POST | 오류 수정 학습 |
| `/api/learn/rules` | GET | 규칙 목록 조회 |
| `/api/learn/autonomous/stats` | GET | 자율 학습 통계 |

### 7. 보안 구현

| 항목 | 구현 | 코드 위치 |
|------|------|----------|
| CORS | localhost만 허용 | `main.py:45-50` |
| Rate Limiting | 분당 20회 | `main.py:52-55` |
| 파일 검증 | 10MB, xls/xlsx만 | `validate.py:30-40` |
| PII 마스킹 | 오류 메시지에서 실제 값 숨김 | `validation_layer1.py` |

---

## 프로젝트 구조

```
WIKISOFT3/
├── external/              # 외부 인터페이스
│   └── api/
│       ├── main.py        # FastAPI 앱 (CORS, Rate Limit)
│       └── routes/
│           ├── validate.py      # 검증 API
│           ├── react_agent.py   # Agent API
│           ├── export.py        # 다운로드 API ✅
│           └── diagnostic.py    # 진단 질문 API
│
├── internal/              # 내부 로직
│   ├── agent/             # AI Agent
│   │   ├── react_agent.py       # ReACT 루프
│   │   ├── tool_registry.py     # 도구 관리
│   │   └── confidence.py        # 신뢰도 계산
│   │
│   ├── ai/                # AI/ML 모듈
│   │   ├── matcher.py           # 헤더 매칭 (핵심)
│   │   ├── llm_client.py        # OpenAI 클라이언트
│   │   └── autonomous_learning.py # 자율 학습 ✅
│   │
│   ├── parsers/           # 파서
│   │   ├── parser.py            # Excel 파싱 + 헤더 탐지 ✅
│   │   └── standard_schema.py   # 표준 스키마
│   │
│   └── validators/        # 검증기
│       ├── validator.py         # 통합 검증
│       ├── validation_layer1.py # 형식 검증
│       ├── validation_layer2.py # 교차 검증
│       └── validation_layer_ai.py # AI 검증 ✅
│
├── frontend/              # React 프론트엔드
│   └── src/
│       ├── App.tsx              # 메인 앱 (접기/펼치기) ✅
│       ├── components/
│       │   ├── SheetEditorPro.tsx  # 스프레드시트 에디터 ✅
│       │   ├── FloatingChat.tsx    # AI 챗 사이드바
│       │   └── ErrorBoundary.tsx   # 에러 핸들링
│       └── lib/
│           └── errorHandler.ts     # 에러 핸들러
│
├── training_data/         # 학습 데이터
│   ├── error_rules.json   # 19개 규칙 + 학습 패턴
│   ├── behavior_logs.json # 행동 로그
│   └── cases/             # 40개 케이스
│       └── index.json     # 182개 헤더 패턴
│
└── tests/                 # 테스트
    ├── test_parser.py
    └── test_matcher.py
```

---

## 빠른 시작

### 1. 프로젝트 클론
```bash
git clone https://github.com/protkjj/wikisoft.git
cd wikisoft
```

### 2. Python 가상환경 설정
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r WIKISOFT3/requirements.txt
```

### 3. 프론트엔드 의존성 설치
```bash
cd WIKISOFT3/frontend
npm install
cd ../..
```

### 4. 서버 시작
```bash
cd WIKISOFT3
./start.sh
```

또는 개별 실행:
```bash
# 터미널 1 - 백엔드 (포트 8003)
cd WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003

# 터미널 2 - 프론트엔드 (포트 3004)
cd WIKISOFT3/frontend
npm run dev
```

브라우저에서 `http://localhost:3004` 접속

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Vite |
| AI | OpenAI GPT-4o-mini |
| Excel | openpyxl, xlrd, pandas |
| 저장소 | JSON (Case Store, Error Rules) |

---

## 학습 데이터 현황

```
총 케이스: 40개
├── 실제 파일: 5개 (1,364명)
│   ├── 세라젬 (750행)
│   ├── 대한싸이로 (86행)
│   ├── 자강산업 (115행)
│   ├── 에이치자산운용 (15행)
│   └── 푸본현대생명 (398행)
└── 합성 데이터: 35개

헤더 패턴: 182개
매핑 성공률: 95%
평균 신뢰도: 81%

검증 규칙: 19개
├── 값 검증 (4개): 급여, 성별 등
├── 날짜 검증 (2개): 생년월일, 입사일
├── 연령 검증 (2개): 미성년, 고령
├── 교차 검증 (3개): 중복, 입사<생년
├── YoY 검증 (3개): 전년 대비 변경
└── 학습된 규칙 (5개): 동적 학습

자율 학습 패턴: 9개
```

---

## 버그 수정 이력 (Final Release)

### 2026.01.03 - Final Fixes

| 이슈 | 원인 | 해결 |
|------|------|------|
| 헤더가 A,B,C,D,E로 표시 | 잘못된 행을 헤더로 인식 | `_find_header_row()` 함수 추가 |
| 의심목록 다운로드 500 에러 | 한글 파일명 인코딩 오류 | `urllib.parse.quote()` 적용 |
| 경고 항목 다운로드 누락 | `severity === 'error'` 필터링 | 필터 제거, 모든 항목 포함 |
| API 404 에러 | 프록시 설정 오류 | `VITE_API_URL=/api` 수정 |

### 2026.01.01 - Phase 3 Refactoring

| 개선 | 변경 내용 |
|------|----------|
| Console.log 정리 | 34개 console 문 제거 |
| 에러 추출 Hook | `useValidationErrors.ts` 추출 |
| 코드 중복 제거 | ~80줄 중복 코드 통합 |

---

## 후속 프로젝트

WIKISOFT3의 핵심 검증 로직은 **WIKISOFT 4.1**로 마이그레이션되었습니다.

v4.1에서 추가된 기능:
- JWT + API Key 인증
- RBAC 5단계 권한 관리
- PII 자동 탐지 및 마스킹
- k-익명화 지원
- n8n 워크플로우 통합
- CloudEvents 웹훅

자세한 내용은 [WIKISOFT4 README](../WIKISOFT4/README.md)를 참조하세요.

---

## 라이센스

Private - 내부 사용 전용

---

## 개발

- **개발**: KJ
- **AI 지원**: Claude (Anthropic)
- **개발 기간**: 2025.12 ~ 2026.01
- **최종 버전**: v3.0 (완결)
