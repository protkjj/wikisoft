# WIKISOFT 명부검증체계 (AI 완전 위임)

AI 챗봇으로 클라이언트 직원 명부 검증 및 자동 수정하는 시스템

## 🎯 목적

- **기존 문제**: 클라이언트가 보낸 직원 명부 엑셀에 오류/양식 불일치로 인한 반복적인 수정 요청
- **솔루션**: AI가 모든 정규화/검증을 자동으로 처리
- **효과**: 코드 유지보수 최소화, 확장성 무한대

## 🏗️ 시스템 구조 (AI 중심)

```
파일 업로드
    ↓
[파일 로드] pandas로 읽기
    ↓
[AI 정규화] LLM이 전화/날짜/급여 자동 변환
    ↓
[AI 검증] LLM이 비즈니스 규칙/이상 감지
    ↓
[세션 저장] 결과 반환
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
cd /Users/kj/Desktop/wikisoft
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수

`.env` 파일 생성:
```bash
OPENAI_API_KEY=your-api-key-here
```

### 3. 백엔드 실행

```bash
source .venv/bin/activate
python -m uvicorn external.api.main:app --reload --port 8000
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

## 📁 폴더 구조

```
wikisoft/
├── README.md
├── PROJECT_SPEC.md        ← 상세 명세
├── REBUILD_GUIDE.md       ← 구현 가이드
├── requirements.txt
├── .env
├── external/
│   └── api/
│       └── main.py        ← FastAPI 백엔드
├── internal/
│   └── ai/                ← AI 통합 (핵심!)
│       ├── client.py
│       └── prompts.py
└── frontend/
    └── src/
        └── components/
```

## 📚 문서

- [PROJECT_SPEC.md](PROJECT_SPEC.md) - 프로젝트 명세서
- [REBUILD_GUIDE.md](REBUILD_GUIDE.md) - 단계별 구현 가이드

## 🔑 핵심 개념

**모든 비즈니스 로직을 AI에게 위임**:
- ✅ 정규화: +82→010, 날짜 형식, 급여 단위 → AI가 자동 처리
- ✅ 검증: 비즈니스 규칙, 이상 감지 → AI가 자동 처리
- ✅ 수정 제안: 자연어로 사용자에게 제안

**우리가 할 일**:
- 파일 업로드/다운로드
- 세션 관리
- AI API 호출
- 그리드 UI

## 📝 할 일

1. [x] 프로젝트 명세 작성
2. [x] 재구축 가이드 작성
3. [x] 폴더 구조 생성
4. [ ] internal/ai/ 구현
5. [ ] external/api/main.py 구현
6. [ ] 프론트엔드 연결
7. [ ] 테스트

---

**복구 완료!** 이제 차근차근 다시 만들면 됩니다! 🚀
