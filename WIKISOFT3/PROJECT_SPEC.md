# 📝 WIKISOFT3 기술 스펙

**작성일**: 2025-12-30  
**버전**: v3 (내부/제한 사용자용, AI 에이전트 친화)  
**상태**: Phase A/B 완료, Phase C 진행 중

---

## 1. 개요

WIKISOFT2의 설계를 **완성**하는 것이 목표. 새로운 것을 추가하기보다 **미완성된 핵심 기능**을 먼저 완성하고, 그 다음 에이전트 고도화로 넘어감.

### 핵심 철학 (WIKISOFT2에서 배운 것)
- **"자연스러운 매칭"이 핵심** - AI는 가속기, 폴백이 기본
- **UX가 기술보다 중요** - 질문 최소화, 뒤로가기, 버튼 위치 고정
- **경고는 차단이 아니라 안내** - 투명성 확보 목적
- **신뢰도 기반 의사결정** - 95% 이상만 자동, 나머지는 확인 요청
- **케이스 학습이 미래** - 100개 파일 처리 후 새 파일은 거의 자동

---

## 2. 범위

### In Scope
- HR/재무 엑셀 파싱, 헤더 매칭, 규칙 검증, 자동 수정/리포트
- 에이전트 자동화(ReACT 루프): 신뢰도 기반 재시도/질문/교차검증
- 배치/비동기 처리: 중간 규모(≤100개 파일 동시, 100k 행급 파일)
- 배포: SaaS 기본 + 온프레/로컬 LLM은 옵션

### Out of Scope
- 다중 대기업 테넌트 동시 운영
- 초대규모 데이터 레이크 통합
- 다국어 확장(한/영 외 언어)

---

## 3. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│   Frontend (React + Vite, Port 3003)                        │
│   - 24개 질문 UI (사이드바 + 메인)                            │
│   - 수동 매핑 UI (TODO)                                      │
│   - 신뢰도/경고 대시보드 (TODO)                               │
├─────────────────────────────────────────────────────────────┤
│   API Layer (FastAPI, Port 8003)                            │
│   - /api/health, /api/diagnostic-questions                  │
│   - /api/validate (auto-validate)                           │
│   - /api/batch-validate, /api/batch-status                  │
├─────────────────────────────────────────────────────────────┤
│   Agent Layer                                               │
│   ├─ Tool Registry (도구 중앙 관리)               ✅ 구현됨    │
│   ├─ Confidence Scorer (신뢰도 계산)              ✅ 구현됨    │
│   ├─ Decision Engine (의사결정)                   🔶 기본만    │
│   └─ Memory/Persistence (케이스 저장)             🔶 기본만    │
├─────────────────────────────────────────────────────────────┤
│   Core Tools                                                │
│   ├─ Parser (Excel/XLS/XLSX)                      ✅ 구현됨    │
│   ├─ AI Matcher (GPT-4o + 폴백)                   ✅ 구현됨    │
│   ├─ Validator (L1 + L2)                          ✅ 구현됨    │
│   └─ Report Generator                             ❌ JSON만    │
├─────────────────────────────────────────────────────────────┤
│   Queue Layer (Redis/RQ with in-memory fallback)            │
│   - 배치 작업 관리                                           │
│   - 진행률 추적                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 현재 진행 상황

### ✅ Phase A 완료: API Layer
| 항목 | 상태 | 비고 |
|------|------|------|
| /api/health | ✅ | 시스템 상태 확인 |
| /api/diagnostic-questions | ✅ | 24개 고정 질문 |
| /api/validate (auto-validate) | ✅ | Tool Registry 연동 |
| /api/batch-validate | ✅ | Redis/in-memory 큐 |
| /api/batch-status/{job_id} | ✅ | 진행률 조회 |

### ✅ Phase B 완료: Agent & Batch
| 항목 | 상태 | 비고 |
|------|------|------|
| Tool Registry | ✅ | 11개 도구 등록 |
| Confidence Scorer | ✅ | 4가지 지표 계산 |
| 스트리밍 파서 | ✅ | XLS/XLSX 지원 |
| Worker 배치 | ✅ | Redis 폴백 포함 |
| 진행률 대시보드 | ✅ | 기본 UI |

### 🔶 Phase C 진행 중: Memory & UX
| 항목 | 상태 | 우선순위 |
|------|------|----------|
| Memory 유사도 검색 | ❌ | 🔴 높음 |
| Excel 출력 (빨강/노랑 셀) | ❌ | 🔴 높음 |
| 수동 매핑 UI | ❌ | 🔴 높음 |
| Few-shot Learning | ❌ | 🔴 높음 |
| 동적 질문 생성 | ❌ | 🟡 중간 |
| Cross-file Learning | ❌ | 🟡 중간 |

### ❌ Phase D 미시작: 배포 준비
| 항목 | 상태 | 우선순위 |
|------|------|----------|
| 텔레메트리 | ❌ | 🟢 낮음 |
| 감사 로그 | ❌ | 🟢 낮음 |
| 한/영 UI 전환 | ❌ | 🟢 낮음 |
| 오프라인/온프레 모드 | ❌ | 🟢 낮음 |

---

## 5. WIKISOFT2 → WIKISOFT3 비교

### 가져온 것 (성공 요소)
| 항목 | WIKISOFT2 | WIKISOFT3 |
|------|-----------|-----------|
| Tool Registry | 11개 도구 | ✅ 동일 |
| 24개 고정 질문 | 유지 | ✅ 동일 |
| AI 헤더 매칭 | GPT-4o + 폴백 | ✅ 동일 |
| Layer 2 검증 | 8개 체크 | ✅ 동일 |
| Confidence Score | 4가지 지표 | ✅ 동일 |

### 완성할 것 (WIKISOFT2 미완성)
| 항목 | WIKISOFT2 상태 | WIKISOFT3 목표 |
|------|---------------|----------------|
| Memory 시스템 | 설계만 | 구현 예정 |
| Few-shot Learning | 미구현 | 구현 예정 |
| Excel 출력 | 빨강/노랑 셀 | 복원 예정 |
| 수동 매핑 UI | 설계만 | 구현 예정 |
| 자동 재시도 | 미구현 | 구현 예정 |

---

## 6. API 명세

### 6.1 Health Check
```http
GET /api/health

Response 200:
{
  "status": "healthy",
  "version": "3.0",
  "timestamp": "2025-12-30T00:00:00"
}
```

### 6.2 Diagnostic Questions
```http
GET /api/diagnostic-questions

Response 200:
{
  "total": 24,
  "questions": [...],
  "note": "24개 고정 질문 (v2 동일)"
}
```

### 6.3 Auto Validate
```http
POST /api/validate
Content-Type: multipart/form-data

Body:
- file: manifest.xlsx
- answers: {"q1": "예", "q21": 17, ...}

Response 200:
{
  "success": true,
  "file_name": "manifest.xlsx",
  "row_count": 750,
  "overall_confidence": 0.75,
  "header_mapping": {...},
  "validation_warnings": [...],
  "decision": {
    "type": "ask_human",
    "reason": "confidence below threshold"
  }
}
```

### 6.4 Batch Validate
```http
POST /api/batch-validate

Response 202:
{
  "job_id": "job-abc-123",
  "status": "processing",
  "total_files": 5
}
```

### 6.5 Batch Status
```http
GET /api/batch-status/{job_id}

Response 200:
{
  "job_id": "job-abc-123",
  "status": "completed",
  "progress": 100,
  "results": [...]
}
```

---

## 7. 성능 목표

| 지표 | 현재 (v3 alpha) | 목표 (v3 stable) |
|------|----------------|------------------|
| **자동화율** | ~30% | 85%+ |
| **처리 시간** | 30분/파일 | 5분/파일 |
| **신뢰도** | 75% | 90%+ |
| **사람 개입** | 70% | 15% |
| **헤더 매칭** | AI 100%, 폴백 77% | 유지 |
| **대용량 처리** | 100k 행 | 유지 |

---

## 8. 신뢰도 기반 의사결정

### 신뢰도 계산 공식
```
Overall = (0.30 × 데이터품질) + (0.25 × 규칙매칭) + 
          (0.20 × 수정안정성) + (0.15 × 케이스유사도) + 
          (0.10 × 모델신뢰도)
```

### 의사결정 테이블
| 신뢰도 | 액션 | 사람 개입 |
|--------|------|----------|
| ≥ 95% | AUTO_COMPLETE | 0% |
| 80-95% | AUTO_CORRECT + 알림 | ~5% |
| 70-80% | AUTO_WITH_REVIEW | ~15% |
| 50-70% | ASK_HUMAN | ~80% |
| < 50% | MANUAL_REVIEW | 100% |

---

## 9. 즉시 실행 TODO

### 이번 주 (Phase C)
1. **Excel 출력 구현** - openpyxl 기반, 빨강/노랑 셀 강조
2. **Memory 유사도 검색** - 키워드 기반 케이스 매칭
3. **수동 매핑 UI 기초** - 드래그앤드롭 또는 select box

### 다음 주
4. **Few-shot 저장소** - 성공 케이스 JSON 저장
5. **동적 질문 생성** - 이상치 감지 시 추가 질문
6. **자동 재시도 로직** - 실패 시 대안 전략

---

## 10. 파일 구조

```
WIKISOFT3/
├── external/api/
│   ├── main.py              # FastAPI 앱
│   └── routes/              # 라우트 모듈
├── internal/
│   ├── agent/               # Tool Registry, Confidence
│   ├── ai/                  # AI 매칭, 질문
│   ├── memory/              # 케이스 저장
│   ├── parsers/             # Excel 파싱
│   ├── queue/               # 배치 작업
│   ├── validators/          # L1/L2 검증
│   └── generators/          # 리포트 생성
├── frontend/src/            # React UI
├── PROJECT_SPEC.md          # 이 문서
├── ARCHITECTURE.md
└── README.md
```

---

## 11. 릴리스 노트

### v3-alpha (현재)
- Tool Registry + Confidence 기본 구현
- 24개 고정 질문 유지
- AI 헤더 매칭 (GPT-4o + 폴백)
- 배치 처리 (Redis/in-memory)
- 프론트엔드 사이드바 레이아웃

### v3-stable (목표)
- Memory 시스템 완성
- Excel 출력 복원
- 수동 매핑 UI
- Few-shot Learning
- 자동화율 85%+ 달성

---

**최종 목표**: WIKISOFT2의 설계를 완성하여 **자동화율 85%, 처리 시간 5분/파일** 달성
