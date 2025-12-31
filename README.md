# 🏢 WIKISOFT 프로젝트

**퇴직연금 컨설팅을 위한 HR/재무 데이터 자동 검증 시스템**

> 사람이 30분 걸리던 엑셀 검증 작업을 AI가 5분 안에 처리합니다.

---

## 📌 이 프로젝트가 하는 일

퇴직연금 컨설팅 업무에서 고객사로부터 받은 **재직자명부, 급여대장** 같은 엑셀 파일을 검증합니다:

1. **파일 업로드** → 엑셀 파일을 드래그앤드롭
2. **자동 분석** → AI가 컬럼 헤더를 인식하고 표준 필드에 매핑
3. **데이터 검증** → 주민번호 형식, 입사일 논리, 급여 이상치 등 체크
4. **결과 리포트** → 오류/경고를 정리해서 보여줌

**핵심 가치**: 수작업을 줄이고, 실수를 방지하며, 검증 기준을 자동으로 학습합니다.

---

## 📂 폴더 구조

```
wiki/
├── WIKISOFT1/          # v1 - 초기 프로토타입 (레거시)
├── WIKISOFT2/          # v2 - 참조용 아키텍처
├── WIKISOFT3/          # v3 - 현재 개발 중 ⭐
│   ├── external/       #   API 서버 (FastAPI)
│   ├── internal/       #   핵심 로직 (AI, 검증, 파서)
│   ├── frontend/       #   웹 UI (React + Vite)
│   └── training_data/  #   학습 데이터
└── data/               # 테스트용 샘플 데이터
```

**현재 작업 중인 버전은 `WIKISOFT3`입니다.**

---

## 🚀 WIKISOFT3 현재 상태 (2026년 1월 기준)

### 완료된 기능 ✅

| 기능 | 설명 |
|------|------|
| **엑셀 파싱** | XLS/XLSX 파일 자동 인식, 헤더 추출 |
| **AI 헤더 매핑** | GPT-4o로 "사번" → `employee_id` 자동 매핑 |
| **3단계 검증** | 규칙 기반 → AI 보조 → 휴리스틱 검증 |
| **자율 학습** | 사용자 피드백으로 검증 규칙 자동 추가 |
| **챗봇** | "이 경고 무시해줘" 같은 자연어 처리 |
| **신뢰도 점수** | 매핑/검증 결과에 대한 확신도 표시 |

### 학습 데이터 📊

- **40개** 검증 케이스 축적
- **182개** 헤더 패턴 학습
- **19개** 검증 규칙 + **9개** 자율 학습 패턴
- **5개 고객사** 실제 데이터로 학습 완료

### 성능 지표 📈

| 지표 | 현재 | 목표 |
|------|------|------|
| 자동화율 | 80% | 90% |
| 매핑 정확도 | 95% | 98% |
| 처리 시간 | ~3분/파일 | <2분/파일 |

---

## ⚡ 빠른 실행

### 1. 백엔드 (포트 8003)
```bash
cd WIKISOFT3
source ../.venv/bin/activate
uvicorn external.api.main:app --reload --port 8003
```

### 2. 프론트엔드 (포트 3004)
```bash
cd WIKISOFT3/frontend
npm install && npm run dev -- --port 3004
```

### 3. 접속
- **웹 UI**: http://localhost:3004
- **API 문서**: http://localhost:8003/docs

---

## 🔮 향후 고려사항

### 1. 워크플로우 자동화 (Windmill 통합)

현재는 API를 직접 호출하는 구조지만, 향후 **Windmill** 같은 워크플로우 엔진과 통합을 고려하고 있습니다:

```
현재:   고객 → 파일 업로드 → WIKISOFT3 API → 결과

향후:   고객 → Windmill 워크플로우 → WIKISOFT3 (MCP 서버) → 결과
              ├── 고객 온보딩
              ├── 서류 수집 자동화
              ├── AI 검증 (WIKISOFT3)
              ├── 계리계산
              └── 리포트 생성
```

**기대 효과:**
- 🔐 **보안 강화** - API가 직접 노출되지 않고 Windmill이 게이트웨이 역할
- ⚡ **안정성 향상** - 큐잉, 재시도, 부분 실패 허용
- 📊 **모니터링** - 실행 이력, 감사 로그 자동화
- 🔄 **자동화 확대** - 파일 업로드부터 최종 리포트까지 원스톱

### 2. MCP (Model Context Protocol) 서버

WIKISOFT3를 **MCP 서버**로 감싸면 AI Agent가 도구로 호출 가능:
- `validate_employee_list` - 재직자명부 검증
- `get_validation_status` - 검증 상태 조회
- `generate_validation_report` - 리포트 생성

### 3. 추가 개선 예정
- [ ] Excel 결과 출력 (오류 셀 하이라이트)
- [ ] 수동 매핑 드래그앤드롭 UI
- [ ] 다국어 지원 (한/영)
- [ ] 오프라인 모드

---

## 🔗 관련 문서

| 문서 | 설명 |
|------|------|
| [WIKISOFT3/README.md](WIKISOFT3/README.md) | 상세 기술 문서 |
| [WIKISOFT3/ARCHITECTURE.md](WIKISOFT3/ARCHITECTURE.md) | 시스템 아키텍처 |
| [WIKISOFT3/PROJECT_SPEC.md](WIKISOFT3/PROJECT_SPEC.md) | API 명세, 기술 스펙 |
| [WIKISOFT3/PROJECT_STRUCTURE.md](WIKISOFT3/PROJECT_STRUCTURE.md) | 파일별 역할 설명 |

---

## 📝 Git 정보

**Repository**: https://github.com/protkjj/wikisoft

| Branch | 설명 |
|--------|------|
| `kangjun` | 현재 개발 브랜치 |
| `main` | 안정 버전 |
| `wikisoft1` | v1 레거시 |
| `wikisoft2` | v2 참조용 |

---

## 💡 핵심 철학

1. **AI는 가속기, 폴백이 기본** - AI 없어도 동작, 있으면 더 똑똑해짐
2. **UX가 기술보다 중요** - 사용자가 이해하기 쉬운 결과 제공
3. **경고는 차단이 아니라 안내** - 투명하게 보여주고 사용자가 판단
4. **케이스 학습이 미래** - 많이 쓸수록 자동화율 상승

---

**최종 목표**: 퇴직연금 컨설팅 데이터 검증의 **90% 자동화** 달성 🎯
