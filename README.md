# WIKISOFT 4.1

> Security-first, Privacy-focused HR/Finance Data Validation Platform

## Overview

WIKISOFT 4.1은 보안과 개인정보보호를 핵심 원칙으로 설계된 HR/Finance 데이터 검증 플랫폼입니다.

### Core Principles

1. **Security by Design** - 암호화, RBAC, 감사 로깅이 기본 내장
2. **Privacy First** - PII 자동 탐지, 마스킹, 익명화 지원
3. **Workflow Native** - n8n, Temporal, Webhook 통합

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

## API Endpoints

### Validation
- `POST /api/auto-validate` - 파일 자동 검증
- `GET /api/diagnostic-questions` - 진단 질문 조회

### Export
- `POST /api/export/xlsx` - Excel 내보내기
- `POST /api/export/errors` - 오류 목록 내보내기

### Privacy (v4)
- `POST /api/v4/privacy/detect` - PII 탐지
- `POST /api/v4/privacy/mask` - 데이터 마스킹
- `POST /api/v4/privacy/anonymize` - 익명화

### Webhook (v4)
- `POST /api/v4/webhook/n8n` - n8n 웹훅
- `POST /api/v4/webhook/generic` - 일반 웹훅

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

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: React 18, TypeScript, Vite
- **AI**: OpenAI GPT-4o
- **Database**: PostgreSQL (optional), Redis (optional)
- **Security**: JWT, AES-256-GCM, RBAC

## Migration from v3

WIKISOFT 4.1은 WIKISOFT 3의 검증 로직을 계승하면서 보안과 개인정보보호 기능을 강화했습니다.

| 기능 | v3 | v4 |
|------|----|----|
| 3계층 검증 | ✅ | ✅ |
| AI 매칭 | ✅ | ✅ |
| ReACT 에이전트 | ✅ | ✅ |
| 헤더 자동 탐지 | ✅ | ✅ |
| JWT 인증 | ❌ | ✅ |
| RBAC | ❌ | ✅ |
| PII 탐지 | ❌ | ✅ |
| 데이터 마스킹 | ❌ | ✅ |
| 감사 로깅 | ❌ | ✅ |
| n8n 통합 | ❌ | ✅ |

## License

Private - All rights reserved

## Author

Kangjun
