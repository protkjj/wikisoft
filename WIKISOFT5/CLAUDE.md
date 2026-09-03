# WIKISOFT 5

> Excel AI + Telegram Bot 기반 명부 검증 시스템

## 컨셉

**기존 WIKISOFT4**: React 웹앱 + FastAPI 백엔드 + AI 검증
**WIKISOFT5**: Excel에서 직접 검증 + Telegram으로 알림/대화

## 구조

```
┌─────────────────┐     ┌─────────────────┐
│   Excel + AI    │     │  Telegram Bot   │
│  (검증 수행)     │ ──→ │  (알림/대화)     │
└─────────────────┘     └─────────────────┘
        │                       │
        │              조회 ↕ HTTP
        │                       │
        │             ┌─────────────────┐
        │             │   WIKISOFT4     │
        │             │  FastAPI :8004  │
        │             └─────────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
            사용자 (담당자)
```

## 폴더 구조

```
WIKISOFT5/
├── tg_bot/            # 텔레그램 봇
│   ├── bot.py         # 메인 봇 핸들러 (엔트리포인트)
│   ├── handlers.py    # 명령어 핸들러
│   ├── api_client.py  # WIKISOFT4 백엔드 API 클라이언트
│   ├── notifications.py # 검증 결과 알림 발송
│   └── config.py      # 설정
├── excel/             # Excel 템플릿/가이드
│   └── formulas.md    # AI 수식 가이드
├── tests/             # 테스트 (네트워크 불필요)
└── .env               # 환경변수
```

> 패키지 이름은 `tg_bot` 이다. `telegram` 은 python-telegram-bot 라이브러리가
> 쓰는 이름이라 충돌을 피하기 위해 분리했다.

## 실행 방법

### Telegram Bot
```bash
cd WIKISOFT5
source ../.venv/bin/activate
python -m tg_bot.bot
```

### 테스트
```bash
cd WIKISOFT5
pytest tests/ -v
```

## 환경 변수

```bash
# .env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# WIKISOFT4 백엔드 연결
WIKISOFT4_API_URL=http://127.0.0.1:8004  # 기본값
WIKISOFT4_API_KEY=wk4_xxxxxxxx           # 선택
WIKISOFT4_API_TOKEN=eyJhbGciOi...        # 선택 (JWT)
WIKISOFT4_API_TIMEOUT=10                 # 초, 기본 10

ANTHROPIC_API_KEY=your-api-key  # Excel AI용 (선택)
```

## WIKISOFT4 연결

봇은 WIKISOFT4의 **WIKISOFT3 호환 공개 경로**를 조회한다. 두 경로 모두
`AuthMiddleware.PUBLIC_PATHS` 에 있어 인증 없이도 동작하며,
`WIKISOFT4_API_KEY` / `WIKISOFT4_API_TOKEN` 을 설정하면 각각
`X-API-Key` / `Authorization: Bearer` 헤더로 전달된다.

| 봇 기능 | 백엔드 엔드포인트 |
|---|---|
| `/check` — 서버 상태 + 최근 20건 집계 + 마지막 검증 | `GET /api/health`, `GET /api/windmill/latest?limit=20` |
| `/recent` — 최근 5건 목록 | `GET /api/windmill/latest?limit=5` |
| 알림 발송 (WIKISOFT4 → 봇) | `integrations/telegram/notifier.py` 가 검증 완료 시 직접 발송 |

### Graceful Degradation

백엔드가 꺼져 있거나 응답이 느려도 봇은 죽지 않는다. 모든 통신 실패는
`BackendUnavailable` 로 정규화되어 사용자에게 한국어 안내 메시지로 표시된다.
`/check` 는 헬스 체크만 성공하면 이력 조회가 실패해도 서버 상태를 보여준다.

## 워크플로우

1. **Excel에서 명부 작성**
   - 템플릿 사용
   - Claude for Sheets 또는 Copilot으로 검증

2. **Telegram 알림 수신**
   - 검증 완료 알림
   - 오류/경고 요약

3. **Telegram에서 상호작용**
   - `/check` - 서버 상태 및 검증 현황 확인
   - `/recent` - 최근 검증 결과 조회
   - `/help` - 도움말
