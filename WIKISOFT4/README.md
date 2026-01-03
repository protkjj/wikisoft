# WIKISOFT 4.1

> Security-first, Privacy-focused HR/Finance Data Validation Platform

## Overview

WIKISOFT 4.1은 보안과 개인정보보호를 핵심 원칙으로 설계된 HR/Finance 데이터 검증 플랫폼입니다.

### Core Principles

1. **Security by Design** - 암호화, RBAC, 감사 로깅이 기본 내장
2. **Privacy First** - PII 자동 탐지, 마스킹, 익명화 지원
3. **Workflow Native** - n8n, Temporal, Webhook 통합

---

## v3 대비 주요 개선사항

### 1. 보안 아키텍처 강화

| 기능 | v3 | v4.1 | 개선 내용 |
|------|----|----|-----------|
| 인증 | API Token | **JWT + API Key** | 토큰 만료, 리프레시 지원 |
| 권한 관리 | 없음 | **RBAC 5단계** | admin/manager/analyst/viewer/guest |
| 암호화 | 없음 | **AES-256-GCM** | 저장 데이터 암호화 |
| 감사 로깅 | 없음 | **전체 액션 추적** | 누가, 언제, 무엇을 했는지 기록 |
| 비밀 관리 | .env 노출 | **Secret Manager** | 런타임 암호화 |

### 2. 개인정보보호 기능 신설

```python
# v3: 개인정보 처리 기능 없음
result = validate(file)  # 민감정보 그대로 노출

# v4.1: PII 자동 탐지 및 마스킹
result = validate(file, mask_pii=True)
# 주민번호: 900101-1234567 → 900101-*******
# 전화번호: 010-1234-5678 → 010-****-5678
# 이름: 김철수 → 김*수
```

**지원 PII 유형:**
- 주민등록번호 (정규식 + 체크섬 검증)
- 전화번호 (휴대폰, 일반전화)
- 이메일 주소
- 계좌번호
- 주소
- 성명

**익명화 옵션:**
- k-익명화 (동일 레코드 k개 이상 보장)
- 범주화 (나이 → 연령대)
- 일반화 (상세주소 → 시/군/구만)

### 3. 워크플로우 통합

**v3**: 단일 파일 검증만 지원

**v4.1**: 자동화 파이프라인 지원

```
파일 업로드 → PII 탐지 → 자동 검증 → 결과 알림 → DB 저장
     ↓           ↓           ↓           ↓         ↓
  Webhook     Privacy     Validator    n8n     Temporal
```

**n8n 통합:**
```json
POST /api/v4/webhook/n8n
{
  "workflow_id": "validation_pipeline",
  "trigger": "file_upload",
  "callback_url": "https://n8n.example.com/webhook/result"
}
```

**CloudEvents 표준 지원:**
```json
{
  "specversion": "1.0",
  "type": "com.wikisoft.validation.completed",
  "source": "/wikisoft4/validator",
  "data": { "validation_id": "...", "status": "ok" }
}
```

### 4. 미들웨어 스택 개선

```
Request → RateLimiter → Auth → Audit → Handler → Response
              ↓           ↓       ↓
          분당 제한   JWT 검증   로그 기록
```

**Rate Limiting:**
- 전역: 1000 req/분
- 사용자별: 100 req/분
- 엔드포인트별: 커스텀 설정

**Audit Logging:**
```json
{
  "timestamp": "2026-01-03T10:00:00Z",
  "user_id": "user_123",
  "action": "VALIDATE_FILE",
  "resource": "file_abc.xlsx",
  "ip": "192.168.1.1",
  "result": "success"
}
```

### 5. 코드 아키텍처 리팩토링

**v3 구조:**
```
WIKISOFT3/
├── external/api/      # API만 분리
└── internal/          # 모든 로직 혼재
```

**v4.1 구조:**
```
WIKISOFT4/
├── core/              # 핵심 모듈 (독립 실행 가능)
│   ├── security/      # 보안 계층
│   ├── privacy/       # 개인정보 계층
│   ├── validators/    # 검증 계층
│   └── ...
├── integrations/      # 외부 연동
│   ├── n8n/
│   ├── temporal/
│   └── webhook/
└── api/v4/            # API 버전 관리
    ├── routes/
    ├── middleware/
    └── schemas/
```

**개선 포인트:**
- 레이어 분리 (core ↔ integrations ↔ api)
- 의존성 주입 패턴
- 타입 힌트 100% 적용
- Pydantic v2 스키마

### 6. 검증 기능 계승 및 개선

**v3에서 마이그레이션된 기능:**
- 3계층 검증 시스템 (L1/L2/AI)
- AI 헤더 매칭 (GPT-4o)
- ReACT 에이전트 패턴
- Few-shot 학습 (40개 케이스, 182개 패턴)

**v4.1 개선:**
- 헤더 행 자동 탐지 (한글 키워드 기반)
- 날짜 형식 자동 보존
- 참고사항/비고 컬럼 자동 필터링
- 더 상세한 에러 메시지

---

## Features

### Security
- JWT + API Key 인증
- Role-Based Access Control (5단계 권한)
- AES-256-GCM 암호화
- 전체 액션 감사 로깅
- 레이트 리미팅

### Privacy
- 주민번호, 전화번호, 이메일 자동 탐지
- 데이터 마스킹 (김철수 → 김*수)
- k-익명화 지원
- 동의 관리

### Validation
- 3계층 검증 시스템
  - Layer 1: 형식 검증 (날짜, 타입, 범위)
  - Layer 2: 교차 검증 (중복, 논리)
  - Layer 3: AI 기반 검증
- 헤더 행 자동 탐지
- ReACT 에이전트 패턴

### Workflow Integration
- CloudEvents 표준 지원
- n8n 웹훅 어댑터
- Temporal 워크플로우 (예정)

---

## Quick Start

### Backend (Port 8004)

```bash
cd WIKISOFT4
source ../.venv/bin/activate
uvicorn api.v4.main:app --reload --port 8004
```

### Frontend (Port 3005)

```bash
cd WIKISOFT4/frontend
npm install
npm run dev
```

### Tests

```bash
cd WIKISOFT4
pytest tests/ -v
```

---

## Project Structure

```
WIKISOFT4/
├── core/
│   ├── security/      # 인증, 암호화, RBAC, 감사
│   ├── privacy/       # PII 탐지, 마스킹, 익명화
│   ├── validators/    # 3계층 검증 시스템
│   ├── parsers/       # Excel/CSV 파싱
│   ├── ai/            # AI 매칭, LLM 클라이언트
│   ├── agent/         # ReACT 에이전트
│   ├── generators/    # 리포트 생성
│   ├── memory/        # 세션, 케이스 저장
│   └── utils/         # 유틸리티
├── integrations/
│   ├── n8n/           # n8n 웹훅 어댑터
│   ├── temporal/      # Temporal 워크플로우
│   └── webhook/       # CloudEvents 웹훅
├── api/v4/
│   ├── routes/        # API 엔드포인트
│   ├── middleware/    # 인증, 감사, 레이트리밋
│   └── schemas/       # Pydantic 모델
├── frontend/          # React/TypeScript UI
├── tests/             # 테스트
└── docs/              # 문서
```

---

## API Endpoints

### Validation
- `POST /api/v4/validate` - 파일 자동 검증 (with PII masking)
- `POST /api/v4/validate/batch` - 배치 검증

### Privacy (v4 신규)
- `POST /api/v4/privacy/detect` - PII 탐지
- `POST /api/v4/privacy/mask` - 데이터 마스킹
- `POST /api/v4/privacy/anonymize` - 익명화

### Webhook (v4 신규)
- `POST /api/v4/webhook/n8n` - n8n 웹훅
- `POST /api/v4/webhook/generic` - 일반 웹훅

### Compatibility (v3 호환)
- `POST /api/auto-validate` - v3 호환 검증
- `GET /api/diagnostic-questions` - 진단 질문 조회
- `GET /api/health` - 헬스 체크

---

## Environment Variables

```bash
# Security
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-byte-key
API_KEY_SALT=your-salt

# AI
OPENAI_API_KEY=your-openai-key

# Database
DATABASE_URL=postgresql://...

# Workflow
N8N_WEBHOOK_SECRET=your-webhook-secret
```

---

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: React 18, TypeScript, Vite
- **AI**: OpenAI GPT-4o
- **Database**: PostgreSQL (optional), Redis (optional)
- **Security**: JWT, AES-256-GCM, RBAC

---

## Migration from v3

WIKISOFT 4.1은 WIKISOFT 3의 검증 로직을 계승하면서 보안과 개인정보보호 기능을 강화했습니다.

| 기능 | v3 | v4.1 | 비고 |
|------|----|----|------|
| 3계층 검증 | ✅ | ✅ | 그대로 유지 |
| AI 매칭 | ✅ | ✅ | GPT-4o |
| ReACT 에이전트 | ✅ | ✅ | 그대로 유지 |
| 헤더 자동 탐지 | ✅ | ✅ | 개선됨 |
| JWT 인증 | ❌ | ✅ | **신규** |
| RBAC | ❌ | ✅ | **신규** |
| PII 탐지 | ❌ | ✅ | **신규** |
| 데이터 마스킹 | ❌ | ✅ | **신규** |
| 감사 로깅 | ❌ | ✅ | **신규** |
| n8n 통합 | ❌ | ✅ | **신규** |
| 익명화 | ❌ | ✅ | **신규** |
| CloudEvents | ❌ | ✅ | **신규** |

---

## Roadmap

### v4.2 (예정)
- [ ] Temporal 워크플로우 완전 통합
- [ ] PostgreSQL 영구 저장
- [ ] Redis 캐싱
- [ ] 대시보드 UI

### v4.3 (예정)
- [ ] 멀티테넌시
- [ ] SSO 지원 (SAML, OIDC)
- [ ] 데이터 보존 정책

---

## License

Private - All rights reserved

---

## Author

Kangjun | 2026.01
