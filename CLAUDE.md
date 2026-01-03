# CLAUDE.md - WIKISOFT 4.1

## Project Overview

WIKISOFT 4.1 is a security-first, privacy-focused HR/Finance data validation platform with workflow automation support.

**Core Principles:**
1. **Security by Design** - Encryption, RBAC, audit logging built-in from day one
2. **Privacy First** - PII detection, masking, anonymization as core features
3. **Workflow Native** - n8n, Temporal, webhook integration for automation

## Architecture

```
WIKISOFT4/
├── core/
│   ├── security/      # Auth, encryption, RBAC, audit
│   ├── privacy/       # PII detection, masking, anonymization
│   └── validators/    # Data validation (migrated from v3)
├── integrations/
│   ├── n8n/          # n8n webhook adapter
│   ├── temporal/     # Temporal workflow support
│   └── webhook/      # Generic webhook (CloudEvents)
├── api/v4/
│   ├── routes/       # API endpoints
│   ├── middleware/   # Auth, logging, rate limiting
│   └── schemas/      # Pydantic models
├── tests/
└── docs/
```

## Build & Run Commands

### Backend (FastAPI on port 8004)
```bash
cd WIKISOFT4
source ../.venv/bin/activate
uvicorn api.v4.main:app --reload --port 8004
```

### Tests
```bash
cd WIKISOFT4
pytest tests/ -v
```

## Security Features

- **Authentication**: JWT + API Key support
- **Authorization**: Role-Based Access Control (RBAC)
- **Encryption**: AES-256-GCM for data at rest
- **Audit**: All actions logged with user, timestamp, action
- **Rate Limiting**: Per-user and per-endpoint limits

## Privacy Features

- **PII Detection**: Auto-detect 주민번호, 전화번호, 이메일, etc.
- **Data Masking**: 김철수 → 김*수, 010-1234-5678 → 010-****-5678
- **Anonymization**: k-anonymity support for exports
- **Consent Management**: Track data processing consent

## Workflow Integration

### n8n Webhook Format
```json
POST /api/v4/webhook/n8n
{
  "workflow_id": "wf_123",
  "trigger": "file_upload",
  "callback_url": "https://n8n.example.com/webhook/result"
}
```

### CloudEvents Format
```json
{
  "specversion": "1.0",
  "type": "com.wikisoft.validation.completed",
  "source": "/wikisoft4/validator",
  "id": "uuid",
  "data": { ... }
}
```

## Environment Variables

```bash
# Security
JWT_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-byte-key
API_KEY_SALT=your-salt

# Database
DATABASE_URL=postgresql://...

# Workflow
N8N_WEBHOOK_SECRET=your-webhook-secret
TEMPORAL_HOST=localhost:7233
```

## Git

- Development branch: `kangjun`
- Main branch: `main`
- Version: 4.1.0
