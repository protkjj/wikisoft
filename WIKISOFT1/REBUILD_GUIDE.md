# 🔄 WIKISOFT 재구축 가이드 (단계별)

이 문서는 프로젝트를 처음부터 다시 실행/구현할 때 따라 하면 되는 실전 단계별 가이드입니다. 15~30분이면 백엔드/프론트 기본 플로우를 재구축할 수 있습니다.

## ✅ 사전 준비
- macOS 기준 경로: 프로젝트 루트는 [wiki/WIKISOFT1](wiki/WIKISOFT1)
- 파이썬 3.10+ 권장, Node.js 18+ 권장
- OpenAI 사용 시 환경변수 `OPENAI_API_KEY` 필요 (선택)

## 1) 파이썬 백엔드 환경 구성
프로젝트 루트에서 가상환경 생성 후 의존성 설치:

```bash
cd ~/Desktop/wiki/WIKISOFT1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

환경변수 파일 생성 (선택):
```bash
cp .env.example .env
```
`.env` 내용 예시:
```bash
OPENAI_API_KEY=your-api-key-here
REQUIRE_SESSION_TOKEN=false
MAX_SESSIONS=50
```

## 2) 백엔드 실행
[external/api/main.py](wiki/WIKISOFT1/external/api/main.py) 기준으로 uvicorn 실행:

```bash
source .venv/bin/activate
python -m uvicorn external.api.main:app --reload --port 8000
```

서버가 뜨면 http://localhost:8000 에서 동작합니다.

## 3) API 빠른 검증 (curl)
테스트용 CSV를 준비하고 업로드/세션 확인/수정/다운로드까지 한 번에 확인합니다.

- 업로드 & 검증 (`/validate`):
```bash
curl -s -X POST \
	-F "file=@/path/to/your.csv" \
	http://localhost:8000/validate
```
응답 예시: `{"session_id":"...","session_token":"...","row_count":...,"columns":[...]}`

- 세션 데이터 조회 (`/session/{session_id}`):
```bash
curl -s "http://localhost:8000/session/<SESSION_ID>"
```
`REQUIRE_SESSION_TOKEN=true` 인 경우 헤더/쿼리로 토큰 제공:
```bash
curl -s -H "Authorization: Bearer <SESSION_TOKEN>" \
	"http://localhost:8000/session/<SESSION_ID>"
```

- 셀 수정 (`/update-cell`):
```bash
curl -s -X POST \
	"http://localhost:8000/update-cell?session_id=<SESSION_ID>&row=0&column=<컬럼명>&value=<새값>"
```

- 자동수정 (`/auto-fix/{session_id}`):
```bash
curl -s -X POST "http://localhost:8000/auto-fix/<SESSION_ID>"
```

- CSV 다운로드 (`/download/{session_id}`):
```bash
curl -L -o output.csv "http://localhost:8000/download/<SESSION_ID>"
```

- 챗봇 (`/chat`):
```bash
curl -s -X POST \
	"http://localhost:8000/chat?session_id=<SESSION_ID>&message=$(python -c 'import urllib.parse; print(urllib.parse.quote("급여 기준 이상치 확인해줘"))')"
```

## 4) OpenAI 연동 활성화 (선택)
- [internal/ai/client.py](wiki/WIKISOFT1/internal/ai/client.py)의 `AIProcessor`는 `OPENAI_API_KEY`가 설정되면 실제 정규화/검증/챗 응답을 수행합니다.
- 프롬프트 규칙은 [internal/ai/prompts.py](wiki/WIKISOFT1/internal/ai/prompts.py)의 `NORMALIZE_AND_VALIDATE_PROMPT` 및 `get_normalize_validate_prompt()`에서 관리합니다.

## 5) 프론트엔드 개발 서버 실행
프론트 루트: [frontend](wiki/WIKISOFT1/frontend)

```bash
cd frontend
npm install
npm run dev
```
개발 서버는 기본적으로 http://localhost:5173 입니다.

## 6) 프론트엔드 단계별 구현 체크리스트
아래 항목을 순서대로 구현하면 전체 플로우가 연결됩니다.

1. 업로드 UI: 파일 선택 → `/validate` 호출 → `session_id`, `session_token` 저장
2. 데이터 렌더링: `/session/{id}`로 데이터 fetch → AG Grid 표 렌더 ([frontend/src/components/SpreadsheetView.tsx](wiki/WIKISOFT1/frontend/src/components/SpreadsheetView.tsx))
3. 셀 수정: 그리드 편집 이벤트에서 `/update-cell` 호출 → 수정 이력 표시 (`modified_cells`)
4. 자동수정: 버튼 클릭 시 `/auto-fix/{id}` 호출 → 표 재로드, `corrections_applied`/`remaining_errors` 표시
5. 챗: 패널에서 `/chat` 호출 → 응답 표시 ([frontend/src/components/ChatBot.tsx](wiki/WIKISOFT1/frontend/src/components/ChatBot.tsx))
6. 다운로드: 버튼/링크로 `/download/{id}` 호출 → UTF-8 BOM CSV 저장

## 7) 엔드포인트 요약
- `POST /validate` — 업로드 파일 검증 및 세션 생성
- `GET /session/{session_id}` — 현재 데이터/컬럼/검증 결과 조회
- `POST /update-cell` — 단일 셀 값 업데이트 (쿼리 파라미터)
- `POST /auto-fix/{session_id}` — AI 정규화 결과를 표에 반영
- `GET /download/{session_id}` — CSV 다운로드 (UTF-8 BOM, RFC5987 filename)
- `POST /chat` — 데이터 맥락 기반 챗 응답

## 8) 토큰 보호 (옵션)
- `.env`에서 `REQUIRE_SESSION_TOKEN=true` 설정 시, 각 요청에
	- 헤더: `Authorization: Bearer <SESSION_TOKEN>` 또는
	- 쿼리: `?token=<SESSION_TOKEN>` 필요

## 9) 트러블슈팅
- `OPENAI_API_KEY` 미설정: AI 경로는 안전 폴백으로 동작 (요약/에러 없음)
- 엑셀 파싱 오류: `openpyxl` 버전 확인, 파일 확장자 `.xlsx/.xls` 또는 `.csv` 사용
- CORS 오류: 프론트 도메인이 백엔드 CORS 허용 목록에 있는지 확인 ([external/api/main.py](wiki/WIKISOFT1/external/api/main.py))

## 10) 다음 작업 제안
- 응답 JSON 스키마를 `pydantic` 모델로 정의하여 프론트-백엔드 계약을 명확화
- 에러 리포트 뷰 추가 (행/열별 오류 리스트, 필터/정렬)
- 업로드 히스토리/세션 목록 화면 추가

---

이 가이드대로 진행하면 업로드 → 검증 → 편집 → 자동수정 → 챗 → 다운로드까지 한 번에 연결됩니다. 필요하면 각 단계 구현을 같이 진행해드릴게요.
