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
        └───────────┬───────────┘
                    ▼
            사용자 (담당자)
```

## 폴더 구조

```
WIKISOFT5/
├── telegram/          # 텔레그램 봇
│   ├── bot.py         # 메인 봇 핸들러
│   ├── handlers.py    # 명령어 핸들러
│   └── config.py      # 설정
├── excel/             # Excel 템플릿/가이드
│   ├── template.xlsx  # 명부 템플릿
│   └── formulas.md    # AI 수식 가이드
├── docs/              # 문서
└── .env               # 환경변수
```

## 실행 방법

### Telegram Bot
```bash
cd WIKISOFT5
source ../.venv/bin/activate
python -m telegram.bot
```

## 환경 변수

```bash
# .env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
ANTHROPIC_API_KEY=your-api-key  # Excel AI용 (선택)
```

## 워크플로우

1. **Excel에서 명부 작성**
   - 템플릿 사용
   - Claude for Sheets 또는 Copilot으로 검증

2. **Telegram 알림 수신**
   - 검증 완료 알림
   - 오류/경고 요약

3. **Telegram에서 상호작용**
   - `/check` - 검증 상태 확인
   - `/help` - 도움말
