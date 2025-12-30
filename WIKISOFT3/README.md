# 🚀 WIKISOFT3

**HR/재무 엑셀 자동 검증 시스템 v3**

> 퇴직급여채무 검증을 위한 AI Agent 기반 자동화 시스템

---

## 📅 최근 업데이트 (2024.12.31)

### ✅ Phase D 진행 - AI Agent 고도화

#### 1. ReACT Agent API 연동
- `/api/auto-validate/react` 엔드포인트 추가
- Think → Act → Observe 루프 기반 자율적 의사결정
- 신뢰도 기반 자동 재시도 및 에스컬레이션
- 추론 과정 투명하게 기록 (`agent_reasoning`)

#### 2. 재시도 전략 모듈 (`retry_strategies.py`)
- **지수 백오프**: API 에러, Rate Limit 대응
- **대안 전략 체인**: 실패 시 다른 방법 자동 시도
  - `STRICT_MATCHING` → `LENIENT_MATCHING` → `ASK_HUMAN`
- **비동기 지원**: `AsyncRetryStrategy` 클래스

#### 3. 동적 질문 생성 (`dynamic_questions.py`)
- 이상치 감지 시 추가 질문 자동 생성
- Unmapped 헤더에 대한 확인 질문
- AI 기반 맥락적 질문 생성

#### 4. 검증 결과 화면 UI 개선
- `ValidationResults.tsx` 신규 컴포넌트
- SVG 게이지 차트로 신뢰도 시각화
- 통계 카드 (분석 행, 컬럼 매핑, 오류, 경고)
- AI 에이전트 추론 과정 타임라인

#### 5. 통합 로깅 시스템 (`logging.py`)
- JSON 형식 구조화된 로깅
- 성능 메트릭 자동 수집
- `@log_function` 데코레이터

#### 6. 테스트 코드 보강
- `test_react_agent.py` - 25+ 테스트 케이스
- ReACT Agent 통합 테스트
- 재시도 전략 단위 테스트

---

### 📊 현재 완성도: **80%** (B+ → A등급 진입)

| 영역 | 완성도 | 주요 구현 |
|------|--------|----------|
| 핵심 기능 | 85% | 파싱, 매칭, 검증, 리포트 |
| 에이전트 자율성 | 75% | ReACT 루프, 재시도 전략 |
| 학습 능력 | 80% | Case Store, Few-shot |
| 안정성 | 80% | 에러 핸들링, 타임아웃 |
| UX | 70% | 검증 결과 UI, 신뢰도 시각화 |

---

## ⚡ 빠른 실행

### 백엔드 + 프론트엔드 동시 실행
```bash
# 터미널 1 - 백엔드 (포트 8003)
cd /Users/kj/Desktop/wiki/WIKISOFT3 && source /Users/kj/Desktop/wiki/.venv/bin/activate && python -m uvicorn external.api.main:app --reload --port 8003

# 터미널 2 - 프론트엔드 (포트 3004)
cd /Users/kj/Desktop/wiki/WIKISOFT3/frontend && npm run dev -- --port 3004
```

그 다음 브라우저에서 `http://localhost:3004` 접속

---

## 🚀 빠른 시작

### 1. 백엔드 실행 (포트 8003)
```bash
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate  # 또는 python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn external.api.main:app --reload --port 8003
```

### 2. 프론트엔드 실행 (포트 3003)
```bash
cd frontend
npm install
npm run dev -- --port 3003
```

### 3. 브라우저 접속
```
http://localhost:3003
```

---

## 🔌 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/health` | GET | 서버 상태 확인 |
| `/api/diagnostic-questions` | GET | 13개 진단 질문 조회 |
| `/api/diagnostic-questions/dynamic` | POST | 동적 질문 생성 |
| `/api/auto-validate` | POST | 파일 검증 (파이프라인) |
| `/api/auto-validate/react` | POST | 파일 검증 (ReACT Agent) |
| `/api/auto-validate/download-excel` | GET | Excel 다운로드 |

---

| Phase | 상태 | 설명 |
|-------|------|------|
| **Phase A** | ✅ 완료 | API Layer (health, questions, validate, batch) |
| **Phase B** | ✅ 완료 | Agent Layer (Tool Registry, Confidence, Worker) |
| **Phase C** | ✅ 완료 | AI Agent 자유 분석, FloatingChat, 학습 데이터셋 |
| **Phase D** | 🔶 진행중 | ReACT Agent, 재시도 전략, 동적 질문, UI 고도화 |

---

## 🎯 핵심 철학

WIKISOFT2에서 배운 것:

1. **"자연스러운 매칭"이 핵심** - AI는 가속기, 폴백이 기본
2. **UX가 기술보다 중요** - 질문 최소화, 뒤로가기, 버튼 위치 고정
3. **경고는 차단이 아니라 안내** - 투명성 확보 목적
4. **신뢰도 기반 의사결정** - 95% 이상만 자동, 나머지는 확인 요청

---

## 🏗️ 아키텍처

```
┌──────────────────────────────────────────────┐
│  Frontend (React + Vite, Port 3003)          │
├──────────────────────────────────────────────┤
│  API Layer (FastAPI, Port 8003)              │
│  /api/health, /api/validate, /api/batch-*    │
├──────────────────────────────────────────────┤
│  Agent Layer                                 │
│  Tool Registry → Confidence → Decision       │
├──────────────────────────────────────────────┤
│  Core Tools                                  │
│  Parser | AI Matcher | Validator | Report    │
├──────────────────────────────────────────────┤
│  Queue Layer (Redis/RQ + in-memory fallback) │
└──────────────────────────────────────────────┘
```

---

## ⚡ 빠른 시작

### 1. 백엔드 실행
```bash
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate
uvicorn external.api.main:app --host 0.0.0.0 --port 8003 --reload
```

### 2. 프론트엔드 실행
```bash
cd /Users/kj/Desktop/wiki/WIKISOFT3/frontend
npm install
npm run dev
```

### 3. 접속
- Frontend: http://localhost:3003
- API Docs: http://localhost:8003/docs

---

## 📋 API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/health | 시스템 상태 |
| GET | /api/diagnostic-questions | 13개 진단 질문 조회 |
| POST | /api/auto-validate | 파일 검증 (진단 답변 포함) |
| POST | /api/batch-validate | 배치 검증 |
| GET | /api/batch-status/{job_id} | 배치 진행률 |
| POST | /api/agent/ask | AI 에이전트 대화 |
| GET | /api/auto-validate/download-excel | Excel 결과 다운로드 |

---

## ✅ 구현 완료

### Phase A: API Layer
- [x] /api/health - 시스템 상태 확인
- [x] /api/diagnostic-questions - 13개 진단 질문
- [x] /api/auto-validate - Tool Registry 연동 검증
- [x] /api/batch-validate - Redis/in-memory 큐
- [x] /api/batch-status - 진행률 조회
- [x] /api/agent/ask - AI 에이전트 대화

### Phase B: Agent & Batch
- [x] Tool Registry - 11개 도구 등록
- [x] Confidence Scorer - 4가지 지표 계산
- [x] AI Matcher - GPT-4o + 폴백
- [x] Layer 1/2 Validator
- [x] 스트리밍 파서 - XLS/XLSX 지원
- [x] Worker 배치 - Redis 폴백 포함
- [x] 프론트엔드 사이드바 레이아웃

### Phase C: AI Agent & UX (2024.12.31 완료)
- [x] **AI Agent 자유 분석** - LLM 기반 데이터 분석
- [x] **Error Check 규칙** - knowledge_base.py에 통합
- [x] **학습 데이터셋 구조** - training_data/ 폴더
- [x] **FloatingChat** - 모든 화면에서 AI 대화
- [x] **고객 질문 생성** - AI가 확인 필요 시 질문
- [x] **자동 수정 제안** - auto_fix 필드
- [x] **진단 질문 13개** - 자동 스크롤, 완료 화면

---

## 📋 TODO (앞으로 구현할 것)

### 🔴 높은 우선순위 (Phase D)

#### 1. 실제 데이터 테스트 & 검증
- [ ] 실제 고객 데이터로 AI 분석 정확도 테스트
- [ ] Error Check 규칙 누락 항목 보완
- [ ] AI 응답 품질 검증 및 프롬프트 개선

#### 2. 학습 데이터 수집 & 파인튜닝
- [ ] AI 응답 + 사람 수정 자동 저장 기능 활성화
- [ ] 충분한 학습 데이터 축적 (100+ 케이스)
- [ ] OpenAI/Anthropic 파인튜닝 또는 Few-shot 개선

#### 3. Excel 출력 개선
- [ ] openpyxl 빨강/노랑 셀 강조
- [ ] 오류 항목 시트 분리
- [ ] 수정 제안 코멘트 삽입

#### 4. 수동 매핑 UI 완성
- [ ] 드래그앤드롭 개선
- [ ] 매핑 결과 저장/불러오기
- [ ] 자주 사용하는 매핑 패턴 학습

### 🟡 중간 우선순위

#### 5. 전년도 vs 당년도 교차 검증
- [ ] 두 파일 동시 업로드
- [ ] 입사일/생년월일/성별 변경 감지
- [ ] 인원 대사 자동화

#### 6. 동적 질문 생성
- [ ] 이상치 감지 시 추가 질문 생성
- [ ] AI가 데이터 보고 필요한 질문 판단

#### 7. Memory 유사도 검색
- [ ] 과거 케이스 검색
- [ ] 유사 패턴 자동 적용
- [ ] 성공 패턴 학습

### 🟢 낮은 우선순위 (나중에)

#### 8. 배포 준비
- [ ] Docker 컨테이너화
- [ ] 클라우드 배포 (AWS/GCP)
- [ ] 텔레메트리 & 모니터링
- [ ] 감사 로그
- [ ] 한/영 UI 전환
- [ ] 오프라인/온프레 모드

---

## 📈 성능 목표

| 지표 | 현재 | 목표 |
|------|------|------|
| 자동화율 | ~50% | **85%+** |
| 처리 시간 | 15분/파일 | **5분/파일** |
| 신뢰도 | 80% | **90%+** |
| 사람 개입 | 50% | **15%** |

---

## 🔐 환경 설정

`.env` 파일 (선택):
```bash
OPENAI_API_KEY=sk-...  # AI 매칭용 (없으면 폴백 사용)
```

---

## 📁 프로젝트 구조

```
WIKISOFT3/
├── external/api/          # FastAPI 서버
│   ├── main.py
│   └── routes/
│       ├── agent.py       # AI 에이전트 대화
│       ├── validate.py    # 파일 검증 + AI 분석
│       └── diagnostic_questions.py
├── internal/              # 핵심 로직
│   ├── agent/             # Tool Registry, Confidence
│   ├── ai/                # AI 매칭, LLM 클라이언트
│   │   ├── llm_client.py  # OpenAI/Anthropic 연동
│   │   ├── knowledge_base.py  # Error Check 규칙 + 학습 데이터
│   │   └── matcher.py     # 헤더 매칭
│   ├── memory/            # 케이스 저장
│   ├── parsers/           # Excel 파싱
│   ├── queue/             # 배치 작업
│   ├── validators/        # L1/L2 검증
│   └── generators/        # 리포트
├── frontend/              # React UI
│   └── src/
│       ├── App.tsx        # 메인 앱
│       ├── ChatBot.tsx    # 진단 질문 위자드
│       └── components/
│           └── FloatingChat.tsx  # AI 채팅 위젯
├── training_data/         # 학습 데이터셋 (파인튜닝용)
│   └── README.md
├── PROJECT_SPEC.md        # 상세 기술 스펙
├── ARCHITECTURE.md        # 아키텍처 문서
└── README.md              # 이 파일
```

---

## 🔗 관련 문서

- [PROJECT_SPEC.md](PROJECT_SPEC.md) - 상세 기술 스펙, API 명세
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처

---

## 📝 Git 정보

**Repository**: https://github.com/protkjj/wikisoft

| Branch | 내용 |
|--------|------|
| main | WIKISOFT3 (현재) |
| wikisoft1 | WIKISOFT1 (레거시) |
| wikisoft2 | WIKISOFT2 (참조용) |

---

**최종 목표**: 퇴직급여채무 검증 **자동화율 85%, 처리 시간 5분/파일** 달성 🎯

---

## 🔄 버전 히스토리

| 날짜 | 버전 | 주요 변경 |
|------|------|----------|
| 2025.12.31 | v3.2 | AI Agent 자유 분석, FloatingChat, 학습 데이터셋 구조 |
| 2025.12.30 | v3.1 | 진단 질문 13개, 수동 매핑 UI, Excel 다운로드 |
| 2025.12.xx | v3.0 | WIKISOFT3 초기 버전, Tool Registry, Batch |
