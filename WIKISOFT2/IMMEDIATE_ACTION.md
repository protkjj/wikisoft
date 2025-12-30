# 🎯 WIKISOFT2 최급선무 우선순위 및 실행 계획

**작성일**: 2025-12-26  
**목표**: AI Agent 자율화를 위한 기초 구축 (v2.2)

---

## 📊 최급선무 우선순위

### TIER 1: 🔴 이번 주 (즉시)

#### 1️⃣ **아키텍처 리팩토링: Tool Registry 개념 도입**
**중요도**: ⭐⭐⭐⭐⭐ (Critical)  
**소요 시간**: 16시간 (2일)  
**담당자**: 아키텍트  
**상태**: 대기

**하는 일**:
```
현재 상태:
external/api/main.py (815줄 모놀리식)
└─ 파싱, 검증, 생성 모두 섞여 있음
   → Tool 재사용 불가능
   → Agent 추가 어려움

개선 후:
external/api/
├── main.py (100줄, API 초기화)
└── internal/
    ├── tools/
    │   ├── __init__.py
    │   ├── registry.py  🆕
    │   ├── parser.py    🆕
    │   ├── validator.py 🆕
    │   ├── analyzer.py  🆕
    │   └── corrector.py 🆕
    └── agent/          🆕
        ├── __init__.py
        ├── react_loop.py       🆕
        ├── decision_engine.py  🆕
        ├── confidence.py       🆕
        └── memory.py           🆕
```

**체크리스트**:
- [ ] `internal/tools/` 폴더 생성
- [ ] `internal/tools/registry.py` 작성 (100줄)
- [ ] 현재 main.py의 파싱/검증 로직을 tools로 이동
- [ ] `internal/tools/parser.py` 작성 (150줄)
- [ ] `internal/tools/validator.py` 작성 (150줄)
- [ ] `internal/tools/analyzer.py` 작성 (100줄)
- [ ] `internal/tools/corrector.py` 작성 (100줄)
- [ ] Tool Registry 테스트 작성

**산출물**:
```
internal/tools/
├── __init__.py
├── registry.py (Tool 관리)
├── parser.py (Excel 파싱)
├── validator.py (검증)
├── analyzer.py (분석)
└── corrector.py (수정)
```

---

#### 2️⃣ **ReACT Loop 기초 구현**
**중요도**: ⭐⭐⭐⭐⭐ (Critical)  
**소요 시간**: 12시간 (1.5일)  
**담당자**: AI 엔지니어  
**상태**: 대기

**하는 일**:
```python
# internal/agent/react_loop.py

async def react_loop(file_path: str, max_steps: int = 10):
    """
    Agent의 자동 실행 루프
    
    1️⃣ THOUGHT: LLM이 상황 분석
    2️⃣ ACTION: 도구 선택
    3️⃣ OBSERVATION: 도구 실행 결과 관찰
    4️⃣ 반복...
    """
    state = AgentState(file_path)
    
    for step in range(max_steps):
        # THOUGHT
        thought = await llm.think(
            current_state=state,
            tools_available=registry.describe()
        )
        
        # ACTION (LLM이 도구 선택)
        action = extract_action_from_llm(thought)
        
        # OBSERVATION
        result = await registry.call(action.name, **action.params)
        state.add_observation(result)
        
        # 완료 확인
        if state.is_complete():
            break
    
    return state.generate_report()
```

**체크리스트**:
- [ ] `internal/agent/react_loop.py` 작성 (150줄)
- [ ] `AgentState` 데이터 모델 정의
- [ ] LLM 호출 로직 구현
- [ ] Action 추출 로직 구현
- [ ] 기본 테스트 작성

**산출물**:
```
internal/agent/
├── __init__.py
└── react_loop.py (ReACT 루프)
```

---

#### 3️⃣ **Confidence Scorer 모델**
**중요도**: ⭐⭐⭐⭐ (High)  
**소요 시간**: 8시간 (1일)  
**담당자**: ML 엔지니어  
**상태**: 대기

**하는 일**:
```python
# internal/agent/confidence.py

class ConfidenceScorer:
    def score(self, state: Dict) -> float:
        """신뢰도 계산 (0.0 ~ 1.0)"""
        
        data_quality = 1.0 - (violations / total_cells)
        rule_match = passed_rules / total_rules
        fix_stability = self.get_past_success_rate()
        case_similarity = self.find_similar_cases()
        model_confidence = llm_score
        
        return (
            0.30 * data_quality +
            0.25 * rule_match +
            0.20 * fix_stability +
            0.15 * case_similarity +
            0.10 * model_confidence
        )
    
    def decide(self, confidence: float) -> str:
        """신뢰도에 따른 액션 결정"""
        if confidence >= 0.95:
            return "AUTO_COMPLETE"
        elif confidence >= 0.80:
            return "AUTO_CORRECT"
        # ...
```

**체크리스트**:
- [ ] `internal/agent/confidence.py` 작성 (120줄)
- [ ] 신뢰도 계산 가중치 결정
- [ ] 의사결정 테이블 정의
- [ ] 테스트 작성

**산출물**:
```
internal/agent/
└── confidence.py (신뢰도 계산 및 의사결정)
```

---

#### 4️⃣ **Decision Engine**
**중요도**: ⭐⭐⭐⭐ (High)  
**소요 시간**: 8시간 (1일)  
**담당자**: 시니어 개발자  
**상태**: 대기

**하는 일**:
```python
# internal/agent/decision_engine.py

class DecisionEngine:
    def decide_next_action(self, state: Dict) -> Action:
        """
        신뢰도 기반 자동 의사결정
        """
        confidence = self.scorer.score(state)
        action_type = self.scorer.decide(confidence)
        
        if action_type == "AUTO_COMPLETE":
            return Action(type='complete')
        elif action_type == "AUTO_CORRECT":
            return Action(type='auto_fix', strategy='optimistic')
        elif action_type == "AUTO_WITH_REVIEW":
            return Action(type='auto_fix', strategy='conservative', notify=True)
        else:
            return Action(
                type='ask_human',
                question=self.formulate_question(state)
            )
```

**체크리스트**:
- [ ] `internal/agent/decision_engine.py` 작성 (100줄)
- [ ] 의사결정 로직 구현
- [ ] 질문 생성 로직
- [ ] 테스트 작성

**산출물**:
```
internal/agent/
└── decision_engine.py (자동 의사결정)
```

---

#### 5️⃣ **Agent API 엔드포인트 추가**
**중요도**: ⭐⭐⭐⭐ (High)  
**소요 시간**: 8시간 (1일)  
**담당자**: 백엔드 개발자  
**상태**: 대기

**하는 일**:
```python
# external/api/routes/agent.py 또는 main.py에 추가

@app.post("/auto-validate")
async def auto_validate(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.8,
    token: str = Depends(verify_token)
):
    """
    완전자율 검증 (파일만 필요!)
    
    → ReACT Loop 실행
    → 신뢰도 기반 자동 의사결정
    → 결과 반환
    """
    content = await validate_file(file)
    
    # ReACT Loop 실행
    result = await react_loop(content)
    
    return {
        "status": "success" | "needs_review",
        "confidence": result.confidence,
        "decisions": result.decisions,
        "human_inputs": result.human_inputs,
        "data": result.corrected_data
    }
```

**체크리스트**:
- [ ] `/auto-validate` POST 엔드포인트 작성
- [ ] 기존 `/validate-with-roster`와 호환성 확인
- [ ] 응답 형식 정의
- [ ] 테스트 작성

**산출물**:
```
새 API:
POST /auto-validate
- 입력: 파일만
- 출력: 자동 의사결정 결과
```

---

#### 6️⃣ **requirements.txt 업그레이드**
**중요도**: ⭐⭐⭐ (Medium)  
**소요 시간**: 2시간  
**담당자**: DevOps  
**상태**: 대기

**하는 일**:
```
현재:
fastapi==0.109.0
pandas>=2.2.0
openai>=1.50.0
...

추가할 것:
langchain>=0.1.0          # Agent 프레임워크 (선택사항)
chromadb>=0.3.0           # Vector DB (메모리 저장소)
redis>=4.5.0              # 세션 & 단기 메모리
numpy>=1.24.0             # 수치 계산
scikit-learn>=1.2.0       # 이상치 탐지

선택사항:
llama-index>=0.8.0        # LangChain 대안
sqlalchemy>=2.0.0         # 감사 로그 DB
```

**체크리스트**:
- [ ] requirements.txt 업데이트
- [ ] `pip install -r requirements.txt` 테스트
- [ ] 호환성 확인
- [ ] 다큐멘테이션 업데이트

**산출물**:
```
requirements.txt (Agent-ready 의존성)
```

---

### TIER 2: 🟡 이번 달 (중기)

#### 7️⃣ **Memory 시스템 (Redis)**
**중요도**: ⭐⭐⭐ (Medium)  
**소요 시간**: 20시간  
**상태**: 계획 단계

#### 8️⃣ **Few-shot Learning 데이터**
**중요도**: ⭐⭐⭐ (Medium)  
**소요 시간**: 15시간  
**상태**: 계획 단계

#### 9️⃣ **모니터링 & 로깅**
**중요도**: ⭐⭐⭐ (Medium)  
**소요 시간**: 12시간  
**상태**: 계획 단계

### TIER 3: 🟢 2-3개월 (중장기)

#### 🔟 **LangChain 통합**
**중요도**: ⭐⭐ (Low, 선택사항)  
**상태**: 계획 단계

#### 1️⃣1️⃣ **완전자동화 (v4.0)**
**중요도**: ⭐⭐⭐⭐⭐ (Critical, 궁극 목표)  
**상태**: 계획 단계

---

## 🗓️ 실행 일정

### Week 1 (12.26~1.1)
```
Day 1-2 (12.26-12.27):
  - Tool Registry 아키텍처 설계
  - 폴더 구조 생성
  - parser.py, validator.py 작성 시작

Day 3-4 (12.30-12.31):
  - analyzer.py, corrector.py 작성
  - registry.py 통합
  - Tool 단위 테스트

Day 5 (1.1):
  - 통합 테스트
  - 문서 작성
  - 1주차 검토
```

### Week 2 (1.2~1.8)
```
Day 1-2 (1.2-1.3):
  - react_loop.py 작성
  - confidence.py 작성

Day 3-4 (1.6-1.7):
  - decision_engine.py 작성
  - /auto-validate API 추가

Day 5 (1.8):
  - 통합 테스트
  - v2.2 베타 릴리즈
```

### 완료 목표
```
목표 날짜: 2025년 1월 8일 (2주)
산출물: v2.2 (Tool Registry + ReACT Loop + Confidence Model)
성과: 반자율 Agent (자동화율 20-30%)
```

---

## 💻 개발 환경 준비

### 필요한 것들
```bash
# 1. Python 3.9+
python3 --version

# 2. 가상환경
python3 -m venv .venv
source .venv/bin/activate

# 3. 현재 의존성 설치
pip install -r requirements.txt

# 4. 새 의존성 준비 (나중에)
# langchain, chromadb, redis 추가
```

### 개발 도구
```bash
# 테스트 실행
pytest tests/

# 코드 검사
black .
pylint **/*.py

# 타입 체크
mypy internal/
```

---

## 📋 체크리스트

### 시작 전 (오늘)
- [x] 현재 상태 분석 완료
- [x] 로드맵 작성 완료
- [x] 아키텍처 설계 완료
- [x] 문서 작성 완료
- [ ] 팀 미팅 (목표 공유)
- [ ] 개발 환경 준비

### Phase 1 완료 조건 (2주)
- [ ] Tool Registry 100% 커버리지
- [ ] ReACT Loop 실행 성공
- [ ] Confidence 모델 정확도 70%+
- [ ] `/auto-validate` API 동작
- [ ] Unit tests 커버리지 70%+
- [ ] v2.2 베타 릴리즈

### 성공 지표
```
현재 (v2.1):           목표 (v2.2 후):
사람 개입: 100%  →    70-80%
처리 시간: 30-60분 →  20-30분
신뢰도: 70%  →        80%+
자동화율: 0%  →       20-30%
```

---

## 🚀 즉시 실행할 액션

### 오늘 할 일 (체크리스트)
```bash
# 1. 폴더 생성
mkdir -p internal/tools
mkdir -p internal/agent

# 2. __init__.py 생성
touch internal/tools/__init__.py
touch internal/agent/__init__.py

# 3. 스켈레톤 파일 생성
touch internal/tools/registry.py
touch internal/tools/parser.py
touch internal/tools/validator.py
touch internal/tools/analyzer.py
touch internal/tools/corrector.py

touch internal/agent/react_loop.py
touch internal/agent/confidence.py
touch internal/agent/decision_engine.py

# 4. 테스트 폴더
mkdir -p tests/tools
mkdir -p tests/agent
touch tests/tools/test_registry.py
touch tests/agent/test_react_loop.py

# 5. git 커밋
git add -A
git commit -m "chore: Agent-ready 아키텍처 준비"
```

### 내일 할 일
```
1. Tool Registry 설계 검토
2. parser.py 구현 시작
3. 팀 미팅 (15분)
```

---

## 📞 연락처 & 에스컬레이션

**문제 발생 시**:
1. 기술 문제 → 아키텍트와 상담
2. 일정 문제 → PM에 보고
3. 리스크 → 리드에게 즉시 보고

---

**최종 목표**: 2025년 Q3 완전자율 AI Agent 달성 🎯
