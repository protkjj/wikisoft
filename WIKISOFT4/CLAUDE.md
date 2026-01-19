# CLAUDE.md - WIKISOFT 4.1

## 프로젝트 개요

**WIKISOFT 4.1**은 퇴직연금 계리평가를 위한 **AI 기반 명부 검증 플랫폼**입니다.

### 핵심 기능
1. **진단 질문 (7섹션 74개)** - 고객사 퇴직연금 제도 정보 수집
2. **엑셀 명부 검증** - 사원명부 자동 파싱 및 3단계 검증
3. **AI 헤더 매칭** - GPT-4o 기반 컬럼명 자동 매핑
4. **교차 검증** - 진단 질문 답변 vs 명부 데이터 비교
5. **검증 리포트** - 오류/경고 목록 및 Excel 다운로드

### 사용 흐름
```
[1단계: 진단 질문] → [2단계: 파일 업로드] → [3단계: 검증 결과] → [4단계: 다운로드]
     7페이지              엑셀 파일            오류/경고 확인         최종 파일
```

---

## 실행 방법

### 백엔드 (FastAPI, 포트 8004)
```bash
cd WIKISOFT4
source ../.venv/bin/activate
PYTHONPATH=$(pwd)/.. uvicorn api.v4.main:app --reload --port 8004
```

### 프론트엔드 (React/Vite, 포트 3005)
```bash
cd WIKISOFT4/frontend
npm install  # 최초 1회
npm run dev
```

### 테스트
```bash
cd WIKISOFT4
pytest tests/ -v
```

---

## 프로젝트 구조

```
WIKISOFT4/
├── api/v4/
│   ├── routes/
│   │   ├── auto_validate.py    # 핵심: 파일 검증 API
│   │   ├── compat.py           # 진단 질문 목록 (74개)
│   │   └── export.py           # 엑셀 다운로드
│   └── main.py                 # FastAPI 앱 진입점
│
├── core/
│   ├── validators/
│   │   ├── validation_layer1.py  # L1: 형식 검증 (필수필드 8개)
│   │   ├── validation_layer2.py  # L2: 교차 검증 (중복, 논리)
│   │   └── validator.py          # 통합 검증 오케스트레이터
│   ├── parsers/
│   │   ├── excel.py             # 엑셀 파싱 (헤더 자동 탐지)
│   │   └── standard_schema.py   # 표준 스키마 정의
│   ├── ai/
│   │   ├── matcher.py           # AI 헤더 매칭 (Few-shot)
│   │   └── llm_client.py        # OpenAI API 클라이언트
│   ├── privacy/
│   │   ├── detector.py          # PII 탐지 (주민번호 등)
│   │   └── masker.py            # 마스킹 (김철수→김*수)
│   └── generators/
│       └── report.py            # 검증 리포트 생성
│
├── frontend/src/
│   ├── App.tsx                  # 메인 앱 (4단계 UI)
│   ├── components/
│   │   ├── DiagnosticWizard.tsx # 7페이지 진단 질문 위자드
│   │   ├── SheetEditorPro.tsx   # 명부 편집기 (핸드손테이블)
│   │   └── ManualMapping.tsx    # 수동 헤더 매핑 UI
│   ├── api.ts                   # API 호출 함수
│   └── types.ts                 # TypeScript 타입 정의
│
└── training_data/               # AI 학습 데이터 (에러 케이스)
```

---

## 진단 질문 구조 (7섹션)

| 섹션 | 제목 | 질문 수 | 설명 |
|-----|------|--------|------|
| 1 | 일반사항 | 6개 | 회사명, 담당자, 연락처 등 |
| 2 | 평가대상/퇴직급여 | 26개 | 재직자수, 퇴직자수, 급여총액 등 |
| 3 | 사외적립자산 | 7개 | DC/DB 적립금 정보 |
| 4 | 제도 주요사항 | 11개 | 급여인상률, 퇴직률, 제도변경 |
| 5 | 할인율 | 11개 | 적용할인율 정보 |
| 6 | 적립비율 | 8개 | 적립 목표 및 현황 |
| 7 | 특이사항 | 5개 | 기타 참고사항 (선택) |

### 그룹 질문 (자동 합계)
- `2-a`: 재직자수 (임원/직원/일용직/기타)
- `2-b`: 퇴직자수 (임원/직원/일용직/기타)
- `2-d`: 퇴직급여충당부채 (기초/설정/지급/기말)
- `2-e`: 연간급여총액 (A: 명부합/B: 연간추정/C: 예산)

---

## 검증 단계

### Layer 1: 형식 검증
**필수 필드 (8개)**
- 사원번호, 성명, 입사일, 급여, 근속년수, 생년월일, 퇴직금계, 직급

**검증 항목**
- 날짜 형식 (YYYY-MM-DD 변환)
- 숫자 범위 (급여: 0~10억, 근속: 0~50년)
- 필수값 누락 체크

### Layer 2: 교차 검증
- 중복 사원번호 탐지
- 입사일 > 생년월일 검증
- 근속년수 계산 검증
- 진단 질문 답변 vs 명부 합계 비교

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v4/diagnostic-questions` | 진단 질문 목록 |
| POST | `/api/v4/auto-validate` | 파일 검증 (multipart) |
| POST | `/api/v4/auto-validate/revalidate` | 수정 후 재검증 |
| GET | `/api/v4/auto-validate/download-excel` | 검증 리포트 다운로드 |
| GET | `/api/v4/auto-validate/download-final-data` | 최종 명부 다운로드 |

---

## 환경 변수

```bash
# .env 파일
OPENAI_API_KEY=sk-...        # AI 매칭용 (없으면 규칙 기반)
JWT_SECRET_KEY=...           # 인증 (옵션)
```

---

## Git 브랜치

- 개발: `kangjun`
- 메인: `main`
- 버전: `4.1.0`

---

## 주요 패턴

### Graceful Degradation
OpenAI API 없이도 규칙 기반 매칭으로 동작

### Session Store
검증 결과를 메모리에 저장 (session_id로 다운로드 시 사용)

### 3-Layer Validation
```
파일 → [L1: 형식] → [L2: 교차] → [L3: AI 보조] → 결과
```

### Few-shot Learning
사용자 수정 사항을 `training_data/`에 저장하여 매칭 정확도 향상
