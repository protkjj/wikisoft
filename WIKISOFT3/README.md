# 🚀 WIKISOFT3

**HR/재무 엑셀 자동 검증 시스템 v3**

> WIKISOFT2의 설계를 완성하여 자동화율 85%, 처리 시간 5분/파일 달성

---

## ⚡ 빠른 실행 (한 번에 실행)

### 백엔드 + 프론트엔드 동시 실행
```bash
# 터미널 1 - 백엔드 (포트 8003)
cd /Users/kj/Desktop/wiki/WIKISOFT3 && source ../.venv/bin/activate && uvicorn external.api.main:app --reload --port 8003

# 터미널 2 - 프론트엔드 (포트 3003)
cd /Users/kj/Desktop/wiki/WIKISOFT3/frontend && npm run dev -- --port 3003
```

그 다음 브라우저에서 `http://localhost:3003` 접속

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


| Phase | 상태 | 설명 |
|-------|------|------|
| **Phase A** | ✅ 완료 | API Layer (health, questions, validate, batch) |
| **Phase B** | ✅ 완료 | Agent Layer (Tool Registry, Confidence, Worker) |
| **Phase C** | 🔶 진행중 | Memory & UX (Excel 출력, 수동 매핑) |
| **Phase D** | ❌ 미시작 | 배포 준비 (텔레메트리, 한/영, 오프라인) |

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
| GET | /api/diagnostic-questions | 24개 질문 조회 |
| POST | /api/validate | 파일 검증 (auto-validate) |
| POST | /api/batch-validate | 배치 검증 |
| GET | /api/batch-status/{job_id} | 배치 진행률 |

---

## ✅ 구현 완료

### Phase A: API Layer
- [x] /api/health - 시스템 상태 확인
- [x] /api/diagnostic-questions - 24개 고정 질문
- [x] /api/validate - Tool Registry 연동 검증
- [x] /api/batch-validate - Redis/in-memory 큐
- [x] /api/batch-status - 진행률 조회

### Phase B: Agent & Batch
- [x] Tool Registry - 11개 도구 등록
- [x] Confidence Scorer - 4가지 지표 계산
- [x] AI Matcher - GPT-4o + 폴백
- [x] Layer 1/2 Validator
- [x] 스트리밍 파서 - XLS/XLSX 지원
- [x] Worker 배치 - Redis 폴백 포함
- [x] 프론트엔드 사이드바 레이아웃

---

## �� TODO (Phase C)

### 높은 우선순위 🔴
- [ ] **Excel 출력** - openpyxl, 빨강/노랑 셀 강조
- [ ] **Memory 유사도 검색** - 케이스 매칭
- [ ] **수동 매핑 UI** - 드래그앤드롭
- [ ] **Few-shot Learning** - 성공 패턴 저장

### 중간 우선순위 🟡
- [ ] 동적 질문 생성 - 이상치 감지 시 추가 질문
- [ ] Cross-file Learning - 여러 파일 학습
- [ ] 자동 재시도 로직 - 실패 시 대안 전략

### 낮은 우선순위 🟢 (Phase D)
- [ ] 텔레메트리
- [ ] 감사 로그
- [ ] 한/영 UI 전환
- [ ] 오프라인/온프레 모드

---

## 📈 성능 목표

| 지표 | 현재 | 목표 |
|------|------|------|
| 자동화율 | ~30% | **85%+** |
| 처리 시간 | 30분/파일 | **5분/파일** |
| 신뢰도 | 75% | **90%+** |
| 사람 개입 | 70% | **15%** |

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
├── internal/              # 핵심 로직
│   ├── agent/             # Tool Registry, Confidence
│   ├── ai/                # AI 매칭
│   ├── memory/            # 케이스 저장
│   ├── parsers/           # Excel 파싱
│   ├── queue/             # 배치 작업
│   ├── validators/        # L1/L2 검증
│   └── generators/        # 리포트
├── frontend/              # React UI
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

**최종 목표**: WIKISOFT2의 설계를 완성하여 **자동화율 85%, 처리 시간 5분/파일** 달성 🎯
