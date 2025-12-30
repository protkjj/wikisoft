# WIKISOFT3 Architecture (초안)

## 상위 구성
- API Layer: FastAPI (`external/api`), 라우트 모듈화(`/health`, `/diagnostic-questions`, `/auto-validate`, `/batch-validate`)
- Agent Layer: Tool Registry + ReACT Planner/Router + Decision/Confidence + Memory(옵션)
- Core Tools: 파서, 헤더 매칭, 검증/룰, 집계, 리포트/Excel 출력
- Frontend: 매핑 UI, 진행률/신뢰도/경고 대시보드, ko/en 전환
- Infra: 기능 플래그, 텔레메트리, 감사 로그, 인증/토큰, 워커 큐(배치)

## 데이터/흐름 (요약)
1) 업로드 → `/auto-validate` → 파서/매칭/검증/리포트 → 결과 반환
2) 배치 → `/batch-validate` → 큐/워커 → 진행률/웹훅/리포트
3) 진단 질문 → `/diagnostic-questions` → 24 고정 질문 + 에이전트 추가 질문(clarification)

## 에이전트 배치
- Tool Registry: 파서/매칭/검증/리포트/집계 도구 정의
- Planner/Router: ReACT 루프에서 도구 선택·순서 결정
- Decision/Confidence: 신뢰도 기반 재시도/질문/폴백 판단
- Memory(옵션): 케이스 유사도, 재실행, 사용자 선호 반영

## 모듈 책임(초안)
- `external/api/routes/*`: HTTP 엔드포인트, 요청/응답 스키마 검증
- `internal/agent/*`: planner/router, decision, confidence, memory
- `internal/ai/*`: LLM 클라이언트, 프롬프트, 임베딩
- `internal/parsers/*`: Excel/CSV 파서, 표준 스키마, 프로필별 파싱
- `internal/validators/*`: 규칙/교차 검증, 신뢰도 산출
- `internal/generators/*`: 리포트/Excel 강조/다운로드
- `internal/config/*`: 환경/플래그/모델 선택
- `internal/utils/*`: 로깅, 추적, 공용 헬퍼

## 단계별 확장 가이드
- Phase A: 건강 체크/질문/단일 검증 API, Tool Registry 골격, 수동 매핑 UI
- Phase B: 스트리밍 파서, 워커 배치, 진행률/경고 대시보드
- Phase C: 메모리/케이스 유사도, 자동 질문 강화, 인간 개입 <10%
- Phase D: 텔레메트리/권한/배포 템플릿, 오프라인/온프레 최적화
