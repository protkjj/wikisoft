# WIKISOFT3 Windmill 통합

Windmill에서 WIKISOFT3 API를 사용하기 위한 스크립트 및 플로우 모음

## 파일 구조

```
windmill/
├── validate_roster.py      # 재직자명부 검증 스크립트
├── ifrs_calculate.py       # IFRS 1019 계산 스크립트
├── notify_slack.py         # Slack 알림 스크립트
├── flow_roster_validation.yaml  # 전체 플로우 정의
└── README.md
```

## 사전 준비

### 1. WIKISOFT3 API 서버 외부 노출

Windmill Cloud에서 로컬 API에 접근하려면 ngrok 사용:

```bash
# 터미널 1: WIKISOFT3 서버 실행
cd WIKISOFT3
source ../.venv/bin/activate
PYTHONPATH=$(pwd) uvicorn external.api.main:app --reload --port 8003

# 터미널 2: ngrok으로 외부 노출
ngrok http 8003
```

ngrok URL 예시: `https://xxxx-xxx-xxx.ngrok-free.app`

### 2. Windmill에 스크립트 등록

1. Windmill (app.windmill.dev) 접속
2. Scripts → New Script 생성
3. 각 스크립트 복사/붙여넣기:
   - `validate_roster.py` → `f/wikisoft3/validate_roster`
   - `ifrs_calculate.py` → `f/wikisoft3/ifrs_calculate`
   - `notify_slack.py` → `f/wikisoft3/notify_slack`

### 3. Slack Webhook 설정 (선택)

1. https://api.slack.com/apps 에서 앱 생성
2. Incoming Webhooks 활성화
3. Webhook URL 복사

## 사용 방법

### 방법 1: 개별 스크립트 실행

Windmill에서 `validate_roster` 스크립트 직접 실행:

```
Inputs:
  - file_url: "https://your-storage.com/roster.xlsx"
  - sheet_type: "재직자"
  - api_url: "https://xxxx.ngrok-free.app"
```

### 방법 2: 플로우 사용

1. Windmill → Flows → Import from YAML
2. `flow_roster_validation.yaml` 내용 붙여넣기
3. 플로우 실행:
   ```
   Inputs:
     - file_url: "https://your-storage.com/roster.xlsx"
     - api_url: "https://xxxx.ngrok-free.app"
     - slack_webhook_url: "https://hooks.slack.com/..."
   ```

## 플로우 흐름

```
파일 URL 입력
     ↓
[validate_roster] 검증
     ↓
  ┌──┴──┐
  ↓     ↓     ↓
auto   needs  rejected
_approve _review
  ↓     ↓     ↓
IFRS   Slack  Slack
계산   (검토) (실패)
  ↓
Slack
(성공)
```

## 분기 조건

| action | 조건 | 다음 단계 |
|--------|------|----------|
| `auto_approve` | 신뢰도 ≥ 90%, 에러 없음 | IFRS 계산 → 성공 알림 |
| `needs_review` | 신뢰도 < 90% 또는 중복 발견 | 검토 요청 알림 |
| `rejected` | 에러 발생 | 실패 알림 |

## 트리거 방법

### 수동 실행
Windmill UI에서 직접 실행

### Webhook 트리거
```bash
curl -X POST "https://app.windmill.dev/api/w/your-workspace/jobs/run/f/wikisoft3/flow_roster_validation" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://storage.com/roster.xlsx",
    "api_url": "https://xxxx.ngrok-free.app",
    "slack_webhook_url": "https://hooks.slack.com/..."
  }'
```

### 스케줄 트리거
Windmill → Schedules → New Schedule 에서 cron 설정

## 환경변수 (선택)

Windmill Variables에 저장하면 매번 입력 안해도 됨:

| 변수명 | 설명 |
|--------|------|
| `WIKISOFT3_API_URL` | API 서버 URL |
| `SLACK_WEBHOOK_URL` | Slack Webhook URL |
