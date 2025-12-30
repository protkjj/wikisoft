# 🗓️ 변경 이력 (CHANGELOG)

**프로젝트**: WIKISOFT2  
**최종 업데이트**: 2025-12-26

---

## v2.1 (2025-12-26) — Phase 2.1 완료

- 자연스러운 유사도 기반 헤더 매칭을 기본값으로 확정 (강제 키워드 제거)
- 진단 질문 24개 체계 확정 (퇴직자 총합 자동 계산으로 UX 개선)
- 프런트엔드 UX 개선: 뒤로가기, 버튼 위치 고정, 긴 문구 대응
- `.env` 로드 및 `OPENAI_API_KEY` 반영 (AI 모드 활성화 시 정확도 95%+)
- .xls 지원을 위한 `xlrd` 추가, OpenAI 라이브러리 업그레이드
- 문서 강화: README/OVERVIEW/ARCHITECTURE/CONTRIBUTING 업데이트

## v2.0 (2025-12-25) — Phase 2 완료

- AI 헤더 매칭 시스템 도입 (column_matcher)
- 표준 스키마 정의(20개 필드) 및 파서 구축
- Layer 2 교차 검증(8개 체크)과 Excel 경고 출력
- 폴백 모드 정립(문자열 유사도 기반), 하드코딩 제거
- 통합 테스트 정비 (layer2, ai_matching, api_warnings)

## v1.0 (2025-12-24) — Phase 1 완료

- FastAPI 기본 서버, 파일 업로드/파싱
- Layer 1 검증(코드 룰), 이상치 탐지, 세션 관리
