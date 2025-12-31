# 🚀 WIKISOFT3

**HR/재무 엑셀 자동 검증 시스템 v3**

> 퇴직급여채무 평가를 위한 재직자 명부 자동 검증 AI Agent

---

## 🎯 프로젝트 목표

**"고객이 제출한 재직자 명부 엑셀 파일을 AI가 자동으로 검증하여, 사람의 개입을 최소화한다"**

### 해결하려는 문제
1. **헤더 불일치**: 고객마다 컬럼명이 다름 (`사번` vs `사원번호` vs `직원코드`)
2. **데이터 품질**: 빈 행, 잘못된 날짜 형식, 중복 데이터
3. **수작업 부담**: 파일마다 수동으로 컬럼 매핑하고 오류 찾기
4. **일관성 부족**: 담당자마다 검증 기준이 다름

### 목표 지표
| 지표 | 목표 | 현재 |
|------|------|------|
| 자동 매핑 정확도 | 95%+ | 95% |
| 수동 개입률 | <5% | ~5% |
| 처리 시간 (파일당) | <3초 | ~2초 |
| 학습 케이스 | 100+ | 40개 |

---

## 📅 최근 업데이트 (2026.01.01)

### ✅ AI 검증 레이어 구현
- **AI 기반 검증**: 진단 질문 컨텍스트 고려 (validation_layer_ai.py)
- **규칙 JSON 관리**: 19개 규칙 + 학습된 패턴 (error_rules.json)
- **컨텍스트 오버라이드**: 임원은 70세 입사도 정상 처리

### ✅ 자율 학습 시스템
- **행동 로깅**: 고객 대화/수정 패턴 자동 기록
- **AI 패턴 분석**: 10개 이벤트마다 자동 학습 판단
- **챗봇 통합**: "오류 아님" 키워드 감지 → 자동 학습
- **학습된 패턴**: 9개 (임원 고령 입사, 계약직 저급여 등)

### ✅ 파서 고도화
- **빈 행 자동 제거**: 사원번호 없는 행 필터링 (2483행 → 86행)
- **날짜 자동 변환**: Excel 직렬번호(36770) → ISO 날짜(2000-09-01)
- **설명 행 필터링**: 참고사항에 설명만 있는 행 제외
- **시트 자동 선택**: `(2-2) 재직자 명부` 우선 선택

### ✅ 매칭 개선
- **불필요 컬럼 무시**: 참고사항, 비고, Unnamed 등 자동 스킵
- **Few-shot Learning**: 40개 케이스, 182개 헤더 패턴 학습
- **매핑률 100%**: 필요한 컬럼 전부 자동 매핑

### ✅ 보안 강화
- CORS 하드닝 (localhost만 허용)
- Rate Limiting (분당 20회)
- 파일 검증 (10MB, xls/xlsx만)
- PII 마스킹 (오류 메시지에 실제 값 노출 방지)

---

## 📊 현재 완성도: **90%**

| 영역 | 완성도 | 상태 |
|------|--------|------|
| 파싱 | 95% | ✅ XLS/XLSX, 빈 행 필터, 날짜 변환 |
| 헤더 매칭 | 95% | ✅ AI + Few-shot + 폴백 |
| 검증 | 90% | ✅ L1/L2/AI, 중복 탐지 |
| 학습 시스템 | 90% | ✅ 케이스 저장, 자율 학습 |
| 보안 | 90% | ✅ CORS, Rate Limit, PII 마스킹 |
| UI | 70% | 🔶 기본 완성, 개선 필요 |
| 리포트 | 60% | 🔶 JSON만, Excel 출력 미완 |

---

## ⚡ 빠른 실행

```bash
# 터미널 1 - 백엔드 (포트 8003)
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003

# 터미널 2 - 프론트엔드 (포트 3004)
cd frontend && npm run dev -- --port 3004
```

브라우저에서 `http://localhost:3004` 접속

---

## 🔌 API 엔드포인트

### 핵심 API
| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/auto-validate` | POST | 파일 업로드 및 자동 검증 |
| `/api/react-agent/validate` | POST | ReACT Agent 기반 검증 |
| `/api/agent/ask` | POST | AI 챗봇 대화 |
| `/api/diagnostic-questions` | GET | 진단 질문 목록 |

### 학습 API
| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/learn/correction` | POST | 오류 수정 학습 |
| `/api/learn/rules` | GET | 규칙 목록 조회 |
| `/api/learn/autonomous/stats` | GET | 자율 학습 통계 |
| `/api/learn/autonomous/analyze` | POST | 수동 학습 트리거 |

### 사용 예시
```bash
# 파일 검증
curl -X POST http://localhost:8003/api/auto-validate \
  -F "file=@재직자명부.xls"

# 결과
{
  "status": "ok",
  "confidence": {"score": 0.85},
  "duplicates": {"has_duplicates": false},
  "steps": {
    "parsed_summary": {"row_count": 86},
    "matches": {"mapped": 12, "unmapped": 0, "ignored": 2}
  }
}
```

---

## 🧠 AI Agent 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│   사용자 (Excel 파일 업로드)                                  │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   Frontend (React + Vite)                                   │
│   • 파일 드래그 앤 드롭                                       │
│   • 검증 결과 시각화                                         │
│   • 수동 매핑 UI                                             │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   API Layer (FastAPI)                                       │
│   • /api/auto-validate                                      │
│   • /api/react-agent/validate                               │
│   • Rate Limiting, CORS, 파일 검증                           │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   AI Agent (ReACT Loop)                                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Think: 파일 분석, 다음 액션 결정                      │   │
│   │    ↓                                                 │   │
│   │  Act: 도구 실행 (파싱/매칭/검증/중복탐지)               │   │
│   │    ↓                                                 │   │
│   │  Observe: 결과 평가, 신뢰도 계산                       │   │
│   │    ↓                                                 │   │
│   │  (반복 or 완료)                                       │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   Core Tools (Tool Registry)                                │
│   • Parser: Excel 파싱, 빈 행 필터, 날짜 변환                 │
│   • Matcher: AI + Few-shot + 규칙 기반 매칭                  │
│   • Validator: L1(형식)/L2(교차) 검증                        │
│   • Duplicate Detector: 완전/유사/의심 중복 탐지              │
│   • Report Generator: 결과 리포트 생성                       │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│   Memory Layer (Case Store)                                 │
│   • 성공 케이스 자동 저장                                     │
│   • Few-shot 예제 조회                                       │
│   • 헤더 패턴 학습                                           │
│   • 42개 케이스, 182개 패턴                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 프로젝트 구조

```
WIKISOFT3/
├── external/              # 외부 인터페이스
│   └── api/
│       ├── main.py        # FastAPI 앱, CORS, Rate Limit
│       └── routes/
│           ├── validate.py      # 검증 API
│           └── react_agent.py   # Agent API
│
├── internal/              # 내부 로직
│   ├── agent/             # AI Agent
│   │   ├── react_agent.py       # ReACT 루프
│   │   ├── tool_registry.py     # 도구 관리
│   │   ├── confidence.py        # 신뢰도 계산
│   │   └── retry_strategies.py  # 재시도 전략
│   │
│   ├── ai/                # AI/ML 모듈
│   │   ├── matcher.py           # 헤더 매칭 (핵심!)
│   │   ├── llm_client.py        # OpenAI 클라이언트
│   │   ├── knowledge_base.py    # 도메인 지식
│   │   └── autonomous_learning.py # 자율 학습 시스템 ✨
│   │
│   ├── parsers/           # 파서
│   │   ├── parser.py            # Excel/CSV 파싱
│   │   └── standard_schema.py   # 표준 스키마 정의
│   │
│   ├── validators/        # 검증기
│   │   ├── validator.py         # 통합 검증
│   │   ├── validation_layer1.py # 형식 검증
│   │   ├── validation_layer2.py # 교차 검증
│   │   └── validation_layer_ai.py # AI 검증 ✨
│   │
│   ├── memory/            # 학습 저장소
│   │   ├── case_store.py        # 케이스 관리
│   │   └── persistence.py       # 영구 저장
│   │
│   └── generators/        # 리포트 생성
│       └── report.py
│
├── frontend/              # React 프론트엔드
│   └── src/
│       ├── App.tsx
│       ├── ValidationResults.tsx
│       └── ManualMapping.tsx
│
├── training_data/         # 학습 데이터
│   ├── error_rules.json   # 19개 규칙 + 학습 패턴 ✨
│   ├── behavior_logs.json # 행동 로그 ✨
│   └── cases/             # 40개 케이스
│       └── index.json     # 182개 헤더 패턴
│
├── scripts/               # 유틸리티 스크립트
│   ├── learn_from_file.py      # 파일에서 학습
│   ├── learn_from_data.py      # 일괄 학습 ✨
│   └── generate_samples.py     # 합성 데이터 생성
│
└── tests/                 # 테스트
    ├── test_parser.py
    ├── test_matcher.py
    └── test_react_agent.py
```

---

## 🔧 핵심 기능 상세

### 1. 스마트 파싱
```python
# 자동으로 처리되는 것들
- 빈 행 제거 (사원번호 없는 행)
- 설명 행 제거 (참고사항에 설명만 있는 행)
- 날짜 변환 (Excel 직렬번호 → ISO 날짜)
- 시트 자동 선택 ((2-2) 재직자 명부 우선)
- 헤더 정규화 (줄바꿈, 공백 제거)
```

### 2. AI 헤더 매칭
```python
# 매칭 우선순위
1. Few-shot (학습된 케이스에서 직접 매핑)
2. AI (GPT-4o 호출)
3. 규칙 기반 (유사도 매칭)

# 무시되는 컬럼
- 참고사항, 비고, 메모
- Unnamed 컬럼
- 구분 (단, 종업원구분/제도구분 등은 매핑됨)
```

### 3. 검증 레이어
```python
# L1: 형식 검증
- 필수 컬럼 존재 확인
- 데이터 타입 검사
- 범위 검사 (나이, 날짜 등)

# L2: 교차 검증
- 중복 탐지 (완전/유사/의심)
- 논리적 일관성 (입사일 < 생년월일 등)
```

### 4. 학습 시스템
```python
# 자동 학습
- 신뢰도 80% 이상 → 자동 케이스 저장
- 헤더 패턴 → index.json에 누적

# 현재 상태
- 42개 케이스 (실제 6개 + 합성 36개)
- 182개 헤더 패턴
```

---

## 🚀 다음 단계 (TODO)

### 🔴 높은 우선순위
1. **Excel 리포트 출력**
   - 오류 셀 빨간색, 경고 셀 노란색 강조
   - 다운로드 기능

2. **수동 매핑 UI 개선**
   - 드래그 앤 드롭 매핑
   - 매핑 저장 및 학습

3. **프론트엔드 UX**
   - 로딩 상태 표시
   - 에러 메시지 개선

### 🟡 중간 우선순위
4. **테스트 커버리지**
   - 핵심 로직 단위 테스트
   - E2E 테스트

5. **성능 최적화**
   - 대용량 파일 스트리밍
   - 캐싱

### 🟢 나중에 (n8n 통합 시점)
> ⏰ **n8n 도입 시점**: 다음 요구사항이 생길 때
> - "파일 업로드되면 팀장에게 알림 보내줘"
> - "승인된 건은 DB에 자동 저장해줘"
> - "월별 검증 통계 리포트 자동 생성해줘"

6. **워크플로우 자동화**
   - 파일 업로드 → 검증 → 알림 → 저장
   - Slack/Email 연동
   - 자동 승인 파이프라인

---

## 🔐 보안

| 항목 | 구현 |
|------|------|
| CORS | localhost만 허용 |
| Rate Limiting | 분당 20회 |
| 파일 검증 | 10MB 제한, xls/xlsx만 |
| PII 마스킹 | 오류 메시지에 실제 값 노출 방지 |

---

## 📚 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Vite |
| AI | OpenAI GPT-4o-mini |
| Excel | openpyxl, xlrd, pandas |
| 저장소 | JSON (Case Store, Error Rules) |

---

## 🧪 테스트

```bash
# 단위 테스트
cd /Users/kj/Desktop/wiki/WIKISOFT3
source ../.venv/bin/activate
pytest tests/ -v

# 특정 파일 검증 테스트
python scripts/learn_from_file.py /path/to/file.xls

# 일괄 학습
python scripts/learn_from_data.py
```

---

## 📈 학습 데이터 현황

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
├── 임원 65세 입사 정상
├── 계약직 저급여 허용
└── 79세 임원/고문 허용
```

---

## 📝 라이센스

Private - 내부 사용 전용

---

## 👥 개발

- **개발**: KJ
- **AI 지원**: Claude (Anthropic)
- **시작일**: 2025.12
- **현재 버전**: v3.0
