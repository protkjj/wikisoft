# 📚 WIKISOFT2 통합 문서 가이드

**작성일**: 2025-12-26  
**버전**: 2.1 + 3.0 로드맵

---

## 🗂️ 문서 구조 및 용도

### 📋 핵심 문서들 (이 순서로 읽기)

```
1️⃣ README_v3.md (10분)
   └─ 누가: 모두
   └─ 뭘: 프로젝트 개요 + AI Agent 로드맵
   └─ 언제: 처음 시작할 때

2️⃣ IMMEDIATE_ACTION.md (5분)
   └─ 누가: 개발자, PM
   └─ 뭘: 이번 주 할 일 (체크리스트)
   └─ 언제: 매일 아침

3️⃣ AGENT_ROADMAP.md (20분)
   └─ 누가: 아키텍트, 시니어 개발자
   └─ 뭘: 상세 로드맵 + Phase별 계획
   └─ 언제: 아키텍처 설계할 때

4️⃣ PROJECT_SPEC_v3.md (30분)
   └─ 누가: 개발자
   └─ 뭘: API 명세, Tool Registry, Decision Engine
   └─ 언제: 코드 작성할 때

5️⃣ REBUILD_GUIDE.md (참고)
   └─ 누가: 신규 개발자
   └─ 뭘: 설치, 실행, 개발 방법
   └─ 언제: 개발 환경 설정할 때

6️⃣ PROJECT_OVERVIEW.md (참고)
   └─ 누가: PM, 비기술진
   └─ 뭘: 비즈니스 가치, 성능 지표
   └─ 언제: 스테이크홀더에게 설명할 때
```

---

## 📊 버전별 로드맵

### 현재 상태 (v2.1) ✅

**완료 기능**:
- ✅ AI 헤더 매칭
- ✅ Layer 2 교차 검증
- ✅ Excel 경고 시스템
- ✅ API 토큰 검증
- ✅ 파일 타입 검증
- ✅ 구조화된 로깅

**한계**:
- ❌ 자동화 불가능 (사람이 모든 질문에 답변)
- ❌ 신뢰도 모델 부재
- ❌ Tool Registry 없음
- ❌ Memory 시스템 없음

**성능**:
```
처리 시간: 30-60분/파일
자동화율: 0%
신뢰도: 70% (폴백 포함)
```

---

### 목표 1단계 (v2.2) 🎯 - 2주

**신규 기능**:
- 🆕 Tool Registry (도구 중앙 관리)
- 🆕 ReACT Loop (자동 실행 루프)
- 🆕 Confidence Scorer (신뢰도 계산)
- 🆕 Decision Engine (자동 의사결정)
- 🆕 `/auto-validate` API

**성과**:
```
반자율 Agent
처리 시간: 20-30분 → 신뢰도 높으면 더 빠름
자동화율: 20-30%
신뢰도: 80%+
사람 개입: 70-80%
```

**할 일** ← **지금 여기**:
```
Week 1: Tool Registry + ReACT Loop 기초
Week 2: Confidence Model + Decision Engine + API
```

---

### 목표 2단계 (v3.0) 🚀 - 2개월

**신규 기능**:
- 🆕 LangChain/LlamaIndex 통합
- 🆕 Memory 시스템 (Redis + Vector DB)
- 🆕 Few-shot Learning
- 🆕 Human-in-the-loop UI
- 🆕 `/batch-validate` API (배치 처리)

**성과**:
```
준자율 Agent
처리 시간: 5-10분/파일
자동화율: 85-90%
신뢰도: 90%+
사람 개입: 10-15%
처리량: 100파일/일 (현재 대비 10배)
```

---

### 목표 3단계 (v4.0) 🤖 - 3개월

**신규 기능**:
- 🆕 자동 리플래닝 (실패 시 전략 변경)
- 🆕 Cross-file 학습 (여러 파일 경험)
- 🆕 자체 검증 메커니즘
- 🆕 Batch 자동 처리 (1000+파일/일)
- 🆕 Admin 대시보드

**성과**:
```
완전자율 Agent
처리 시간: 1분/파일
자동화율: 95%+
신뢰도: 95%+ (전문가 수준)
사람 개입: <5% (예외만)
처리량: 1000+파일/일 (현재 대비 60배)
```

---

## 🎯 최급선무 TOP 6

### 1️⃣ Tool Registry (16시간)
**목적**: 도구 중앙 관리, Agent 로직 추가 용이  
**산출물**: `internal/tools/registry.py`

### 2️⃣ ReACT Loop (12시간)
**목적**: Agent 자동 실행 루프  
**산출물**: `internal/agent/react_loop.py`

### 3️⃣ Confidence Scorer (8시간)
**목적**: 신뢰도 기반 의사결정  
**산출물**: `internal/agent/confidence.py`

### 4️⃣ Decision Engine (8시간)
**목적**: 자동 의사결정 로직  
**산출물**: `internal/agent/decision_engine.py`

### 5️⃣ `/auto-validate` API (8시간)
**목적**: 파일만으로 자동 검증  
**산출물**: 새 API 엔드포인트

### 6️⃣ requirements.txt 업그레이드 (2시간)
**목적**: Agent 의존성 추가  
**산출물**: 업데이트된 `requirements.txt`

**합계**: 2주, 54시간

---

## 🔄 개발 프로세스

### Daily (매일)
```
1. IMMEDIATE_ACTION.md 확인
2. 어제 진행상황 정리
3. 오늘 할 일 선택
4. 코드 작성 → 테스트
5. Git 커밋
```

### Weekly (매주)
```
월요일:
  - 주간 계획 수립
  - IMMEDIATE_ACTION.md 업데이트

금요일:
  - 주간 검토
  - 다음주 계획 수정
  - Pull Request 리뷰
```

### Bi-weekly (2주마다)
```
- Phase 완료 검증
- 버전 릴리즈 준비
- 로드맵 업데이트
```

---

## 📈 성공 지표

### Phase 1 (v2.2) 성공 기준
```
✅ Tool Registry 100% 커버리지
✅ ReACT Loop 실행 성공
✅ Confidence 모델 정확도 70%+
✅ `/auto-validate` API 동작
✅ Unit tests 커버리지 70%+
✅ 자동화율 20-30% 달성
```

### Phase 2 (v3.0) 성공 기준
```
✅ LangChain 통합 완료
✅ Memory 시스템 성능 테스트
✅ Few-shot 예제 50+ 수집
✅ Human-in-the-loop UI 완성
✅ `/batch-validate` API 동작
✅ 자동화율 85-90% 달성
```

### Phase 3 (v4.0) 성공 기준
```
✅ 리플래닝 알고리즘 정확도 90%+
✅ Cross-file 학습 구현
✅ 자체 검증 메커니즘 신뢰도 95%+
✅ Batch 처리 1000파일/일
✅ 자동화율 95%+ 달성
```

---

## 🚨 리스크 관리

### 리스크 1: 일정 지연
```
원인: 기술적 복잡도 저평가
대응: 
  - Weekly 리뷰에서 진도 확인
  - 늦으면 Phase 순서 조정
  - 우선순위 재결정
```

### 리스크 2: LLM API 비용 폭증
```
원인: ReACT Loop에서 반복 호출
대응:
  - 캐싱 구현
  - 배치 API 사용
  - 저비용 모델 대체
```

### 리스크 3: 신뢰도 모델 실패
```
원인: 예상과 다른 데이터 분포
대응:
  - Few-shot 데이터 추가
  - 프롬프트 재설계
  - 도구 정확도 개선
  - Fallback 보장 (실패 안 함)
```

---

## 💡 핵심 원칙

### 1. **Autonomous-First**
- 기본: 자동 실행
- 예외: 사람 개입
- 반대는 위험!

### 2. **Transparent**
- 모든 의사결정 로깅
- "왜?" 질문에 답변 가능
- Explainability 최우선

### 3. **Learnable**
- 처음 10개 파일: 인간 가이드 필요
- 100개 후: 거의 자동
- 1000개 후: 전문가 수준

### 4. **Fail-Safe**
- 신뢰도 낮으면 무조건 사람에게 문의
- 손실 함수 비대칭 (false positive > false negative)
- 결과 재검증

### 5. **Cost-Aware**
- 도구별 비용(시간, 토큰) 추적
- 최소 비용 경로 선택
- 배치 처리로 최적화

### 6. **Observable**
- 모든 단계의 메트릭 기록
- 성능 대시보드
- 이상 탐지

---

## 📖 각 문서 목차

### README_v3.md
- 현재 상태 (v2.1)
- 미래 로드맵 (v3.0, v4.0)
- 빠른 시작
- 주요 기능
- 아키텍처 변화

### IMMEDIATE_ACTION.md
- 최급선무 우선순위
- 실행 일정 (2주)
- 체크리스트
- 개발 환경 준비

### AGENT_ROADMAP.md
- Executive Summary
- Phase별 상세 계획 (1, 2, 3)
- 마일스톤 & 일정
- 비용 vs 효과
- 리스크 & 대응

### PROJECT_SPEC_v3.md
- 시스템 아키텍처 (레이어 구조)
- API 명세 (현재 + 미래)
- Tool Registry 명세
- Decision Engine 알고리즘
- 데이터 모델
- 보안 명세
- 성능 지표
- 테스트 전략

---

## 🎬 시작하기

### 지금 바로
```bash
# 1. 최급선무 확인
cat IMMEDIATE_ACTION.md

# 2. 아키텍처 이해
cat AGENT_ROADMAP.md

# 3. 기술 상세 확인
cat PROJECT_SPEC_v3.md

# 4. 개발 환경 준비
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 이번 주
```bash
# 1. 폴더 구조 생성
mkdir -p internal/{tools,agent}

# 2. Tool Registry 설계 검토
vim internal/tools/registry.py

# 3. 팀 미팅 (목표 공유)
# 3. Parser 구현 시작
```

### 이번 달
```
Week 1-2: Phase 1 (Tool Registry, ReACT, Confidence)
Week 3-4: Phase 1 완료 + Phase 2 시작
         (Memory, LangChain)
```

---

## 🤝 협업 가이드

### 역할별 책임

**아키텍트**:
- Tool Registry 설계
- 전체 아키텍처 리뷰
- 기술 결정

**AI 엔지니어**:
- LLM 통합
- ReACT Loop 구현
- Prompt 최적화

**백엔드 개발자**:
- API 구현
- Tool 구현
- 데이터베이스

**ML 엔지니어**:
- Confidence 모델
- 이상치 탐지
- 성능 튜닝

**DevOps**:
- 배포 자동화
- 모니터링
- 스케일링

### 소통 채널
```
일일: Slack (진도 업데이트)
주간: 회의 (이번 주 계획)
양주: 리뷰 (Phase 완료 검증)
```

---

## 📞 더 알아보기

**기술 질문**: 아키텍트, 시니어 개발자  
**일정 문제**: PM  
**리스크**: 팀 리드  

---

## 🎯 최종 목표

**2025년 Q3: 완전자율 AI Agent 달성**

```
현재:                   목표:
시간: 30-60분/파일  →  1분/파일 (60배 빠름)
개입: 100%          →  5% (거의 자동)
신뢰도: 70%         →  95%+ (전문가)
처리량: 10파일/일   →  1000파일/일
```

---

**이 문서들이 당신의 여정을 가이드할 것입니다. 화이팅! 🚀**
