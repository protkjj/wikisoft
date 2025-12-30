# 🤖 WIKISOFT2 AI Agent 자율화 로드맵

**버전**: 1.0  
**작성일**: 2025-12-26  
**최종 목표**: 완전자율 AI Agent (v4.0, 2025년 Q3)

---

## 📊 Executive Summary

### 현재 상태 (v2.1)
- **사람 개입**: ~100% (모든 질문에 직접 답변)
- **처리 시간**: 30-60분/파일
- **신뢰도**: ~70% (폴백 포함)
- **확장성**: 선형 (경험 증가 안 함)

### 목표 상태 (v4.0)
- **사람 개입**: ~5% (예외만)
- **처리 시간**: 1분/파일 (**60배 빠름**)
- **신뢰도**: 95%+ (전문가 수준)
- **확장성**: 초선형 (경험으로 성능 증가)

---

## 🎯 Phase별 계획

### **Phase 1: Foundation (2주, v2.2)**

#### 목표
- Tool Registry 구축
- ReACT Loop 기초
- Confidence 모델
- Decision Engine

#### 상세 작업

**1. Tool Registry (도구 중앙 관리)**
```python
# internal/tools/registry.py
class ToolRegistry:
    """
    모든 Agent가 사용할 수 있는 도구 중앙 관리
    """
    
    def __init__(self):
        self.tools = {
            "parse_excel": ParseExcelTool(),
            "validate_data": ValidateDataTool(),
            "detect_anomalies": AnomalyDetectorTool(),
            "auto_correct": AutoCorrectTool(),
            "estimate_confidence": ConfidenceTool(),
            "generate_report": ReportGeneratorTool(),
        }
    
    def call(self, tool_name: str, **kwargs):
        """도구 실행"""
        return self.tools[tool_name].execute(**kwargs)
    
    def describe(self):
        """Agent가 사용할 도구 설명 (LLM 프롬프트용)"""
        return {
            tool_name: tool.description
            for tool_name, tool in self.tools.items()
        }
```

**2. ReACT Loop (Reasoning + Acting)**
```python
# internal/agent/react_loop.py
async def react_loop(file_path: str, max_steps: int = 10):
    """
    Agent의 사고과정 + 행동 루프
    
    1. THOUGHT: LLM이 상황 분석
    2. ACTION: 다음 도구 선택
    3. OBSERVATION: 도구 실행 결과
    4. 반복
    """
    state = AgentState(file_path)
    
    for step in range(max_steps):
        # 1️⃣ THOUGHT
        thought = await llm.think(state)
        
        # 2️⃣ ACTION (LLM이 도구 선택)
        action = extract_action(thought)
        
        # 3️⃣ OBSERVATION
        result = await tool_registry.call(action.name, **action.params)
        state.add_observation(result)
        
        # 4️⃣ 완료 확인
        if state.is_complete():
            break
    
    return state.generate_report()
```

**3. Confidence Scorer (신뢰도 계산)**
```python
# internal/agent/confidence.py
class ConfidenceScorer:
    """신뢰도 기반 의사결정"""
    
    def score(self, state: Dict) -> float:
        """
        종합 신뢰도 = 
            30% × 데이터_품질 +
            25% × 검증_규칙 +
            20% × 수정_안정성 +
            15% × 사례_유사도 +
            10% × 모델_신뢰도
        """
        return (
            0.30 * self.data_quality(state) +
            0.25 * self.rule_match(state) +
            0.20 * self.fix_stability(state) +
            0.15 * self.case_similarity(state) +
            0.10 * self.model_confidence(state)
        )
    
    def decide(self, confidence: float) -> str:
        """신뢰도에 따른 액션 결정"""
        if confidence >= 0.95:
            return "AUTO_COMPLETE"
        elif confidence >= 0.80:
            return "AUTO_CORRECT"
        elif confidence >= 0.70:
            return "AUTO_WITH_REVIEW"
        else:
            return "ASK_HUMAN"
```

**4. Decision Engine (자동 의사결정)**
```python
# internal/agent/decision_engine.py
class DecisionEngine:
    """Agent가 매 단계마다 다음 액션 결정"""
    
    def decide(self, state: Dict) -> Action:
        confidence = self.scorer.score(state)
        action_type = self.scorer.decide(confidence)
        
        if action_type == "AUTO_COMPLETE":
            return Action(type='complete')
        elif action_type == "AUTO_CORRECT":
            return Action(
                type='auto_fix',
                strategy='optimistic',
                notify=False
            )
        elif action_type == "AUTO_WITH_REVIEW":
            return Action(
                type='auto_fix',
                strategy='conservative',
                notify=True
            )
        else:
            return Action(
                type='ask_human',
                question=self.formulate_question(state)
            )
```

#### 결과물
- ✅ `internal/tools/registry.py` (도구 관리)
- ✅ `internal/agent/react_loop.py` (자동화 루프)
- ✅ `internal/agent/confidence.py` (신뢰도)
- ✅ `internal/agent/decision_engine.py` (의사결정)
- ✅ `POST /auto-validate` (새 API)

#### 성과
```
반자율 Agent
- 자동화율: 20-30%
- 사람 개입: 70-80%
- 처리 시간: 20-30분/파일
```

---

### **Phase 2: Intelligence (2개월, v3.0)**

#### 목표
- LangChain/LlamaIndex 통합
- Memory 시스템 (Redis + Vector DB)
- Few-shot learning
- Human-in-the-loop UI

#### 상세 작업

**1. LangChain 통합**
```python
# internal/agent/langchain_agent.py
from langchain.agents import initialize_agent
from langchain.tools import Tool

class WIKISoftLangChainAgent:
    def __init__(self):
        self.agent = initialize_agent(
            tools=[...],
            llm=ChatOpenAI(model="gpt-4"),
            agent="zero-shot-react-description"
        )
```

**2. Memory 시스템**
```python
# internal/agent/memory.py
class AgentMemory:
    """Agent의 학습 기억소"""
    
    def __init__(self):
        self.short_term = Redis()  # 현재 작업
        self.long_term = Chroma()  # 학습한 패턴
        self.audit_log = PostgreSQL()  # 모든 의사결정
    
    def learn_pattern(self, pattern: Dict):
        """과거 케이스로부터 학습"""
        embedding = self.embed(pattern)
        self.long_term.add(pattern, embedding)
    
    def retrieve_similar(self, context: Dict):
        """유사한 과거 사례 조회"""
        return self.long_term.search(self.embed(context), top_k=5)
```

**3. Few-shot Learning**
```python
# 상황별 프롬프트 최적화
# 예: "임원 인원 수정" 패턴을 본 적 있으면
#     새로운 "임원 인원" 문제는 빠르게 해결

FEWSHOT_EXAMPLES = {
    "employee_count_anomaly": [
        {"input": ..., "reasoning": ..., "action": ...},
        {"input": ..., "reasoning": ..., "action": ...},
        ...
    ],
    "salary_distribution_anomaly": [...],
    ...
}
```

**4. Human-in-the-Loop UI**
```typescript
// frontend/src/components/HumanReview.tsx
<HumanReviewPanel>
  <Question
    id="q21"
    title="임원 인원 수정 확인"
    description="자동으로 17명으로 수정했습니다"
    options={["승인", "거절", "수동 입력"]}
    confidence={0.87}
    riskLevel="medium"
  />
</HumanReviewPanel>
```

#### 결과물
- ✅ `internal/agent/langchain_agent.py`
- ✅ `internal/agent/memory.py`
- ✅ `internal/tools/few_shot_examples.json`
- ✅ Human-in-the-loop UI (React)
- ✅ `POST /batch-validate` (배치 API)

#### 성과
```
준자율 Agent
- 자동화율: 85-90%
- 사람 개입: 10-15%
- 처리 시간: 5-10분/파일 (3배 빠름)
- 신뢰도: 85%+
```

---

### **Phase 3: Autonomy (3개월, v4.0)**

#### 목표
- 완전자동화 (5% 이하 개입)
- Cross-file 학습
- 자체 검증
- Batch 처리 (대량 파일)

#### 상세 작업

**1. 자동 리플래닝**
```python
# 실패 시 전략 변경
if task_failed:
    # 다른 도구 조합 시도
    new_plan = await agent.replan(state, failed_action)
    # 예: auto_correct 실패 → ask_human
```

**2. Cross-File Learning**
```python
# 여러 파일 경험으로 학습
# 100개 파일 처리 후, 새로운 유사 파일은 거의 자동
patterns_learned = 0
for file in files:
    result = await agent.process(file)
    patterns_learned += result.num_new_patterns
    
    if patterns_learned > 50:
        confidence += 0.15  # 신뢰도 증가
```

**3. 자체 검증 메커니즘**
```python
# Agent가 자신의 결정을 검증
result = await agent.auto_fix()
# 다시 검증해서 맞는지 확인
validation = await validator.validate(result)

if validation.score > 0.95:
    # 신뢰도 높으면 바로 반환
    return result
else:
    # 낮으면 사람에게 문의
    return await ask_human()
```

**4. Batch Processing**
```python
# 대량 파일 자동 처리
POST /batch-validate
[
    file1.xlsx, file2.xlsx, ..., file1000.xlsx
]

# Agent가 병렬로 처리 (동시성 관리)
# 신뢰도 높은 것부터 자동 완료
# 신뢰도 낮은 것만 대기열에 (사람이 처리)
```

#### 결과물
- ✅ `internal/agent/replanning.py`
- ✅ `internal/agent/cross_file_learning.py`
- ✅ `internal/agent/self_validation.py`
- ✅ Batch processing engine
- ✅ Admin dashboard

#### 성과
```
완전자율 Agent
- 자동화율: 95%+
- 사람 개입: <5% (예외만)
- 처리 시간: 1분/파일 (60배 빠름)
- 신뢰도: 95%+
- 대량 처리: 1000+파일/일
```

---

## 🔄 마일스톤 & 일정

### Timeline
```
Week 1-2    │ Phase 1: Tool Registry + ReACT Loop
            │ 💾 v2.2 릴리즈
            │
Week 3-4    │ Phase 2 시작: LangChain, Memory
            │
Month 2     │ Phase 2 마무리: Few-shot, UI
            │ 💾 v3.0 베타 릴리즈
            │
Month 3     │ Phase 3: 리플래닝, Cross-file 학습
            │
Month 4     │ Phase 3 마무리: 완전자동화
            │ 💾 v4.0 정식 릴리즈
```

### 릴리즈 버전
```
v2.1 (현재)     기본 검증 시스템
v2.2 (2주)      Tool Registry + ReACT (반자율 Agent)
v3.0 (2개월)    Memory + 학습 (준자율 Agent)
v4.0 (3개월)    완전자동화 (완전자율 Agent)
```

---

## 💰 비용 vs 효과

### 개발 비용
```
Phase 1: 80시간 (2주)
Phase 2: 160시간 (4주)
Phase 3: 200시간 (5주)
─────────────────────
합계: ~450시간 (약 3개월)
```

### 효과 (연간)
```
처리 시간 절감
- 현재: 30분/파일 × 1000파일/년 = 500시간/년
- v4.0: 1분/파일 × 1000파일/년 = 17시간/년
- 절감: 483시간/년 (97% 감소)

비용 절감 (시급 $50 기준)
- 절감액: 483시간 × $50 = $24,150/년

ROI
- 개발 비용: 450시간 × $50 = $22,500
- 연간 절감: $24,150
- **Year 1 ROI: 107%** 🎯
```

---

## ⚠️ 리스크 & 대응

### Risk 1: LLM API 비용 증가
```
문제: Agent 루프에서 LLM 호출 반복
대응:
- 캐싱 (동일 쿼리는 저장된 답변 재사용)
- 배치 API (여러 요청을 한 번에 처리)
- 저비용 모델 대체 (GPT-4 → GPT-3.5 필요시)
```

### Risk 2: 자율화 실패 (신뢰도 낮음)
```
문제: 의외로 신뢰도가 올라가지 않는 경우
대응:
- Few-shot learning 데이터 추가
- 프롬프트 재설계
- 도구 정확도 개선
- Fallback to 사람 (실패 안 함)
```

### Risk 3: 메모리 폭발 (Vector DB 크기)
```
문제: 패턴이 계속 쌓여서 검색 느려짐
대응:
- 정기적 클러스터링 (비슷한 패턴 통합)
- 오래된 데이터 정리
- 효율적인 인덱싱
```

---

## 📋 체크리스트

### Phase 1 완료 조건
- [ ] Tool Registry 100% 커버리지
- [ ] ReACT Loop 실행 성공
- [ ] Confidence 모델 정확도 70%+
- [ ] `/auto-validate` API 동작
- [ ] Unit tests 커버리지 70%+

### Phase 2 완료 조건
- [ ] LangChain 통합 완료
- [ ] Memory 시스템 성능 테스트
- [ ] Few-shot 예제 50+ 수집
- [ ] Human-in-the-loop UI 완성
- [ ] 자동화율 85%+ 달성

### Phase 3 완료 조건
- [ ] 리플래닝 알고리즘 정확도 90%+
- [ ] Cross-file 학습 구현
- [ ] 자체 검증 메커니즘 신뢰도 95%+
- [ ] Batch 처리 1000파일/일 처리
- [ ] 최종 자동화율 95%+ 달성

---

## 🚀 시작하기

### 즉시 할 일 (이번 주)
```bash
# 1. 폴더 구조 설계
mkdir -p internal/{tools,agent}

# 2. Tool Registry 스켈레톤
touch internal/tools/registry.py

# 3. ReACT Loop 스켈레톤
touch internal/agent/react_loop.py

# 4. requirements.txt 업데이트
pip install langchain chromadb redis
```

### 다음 주
```bash
# 1. Tool Registry 구현
# 2. ReACT Loop 구현
# 3. Confidence Scorer 구현
# 4. 테스트 작성
```

---

## 📚 참고 자료

- [ReACT: Synergizing Reasoning and Acting](https://arxiv.org/abs/2210.03629)
- [LangChain Documentation](https://python.langchain.com/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Self-Consistency CoT](https://arxiv.org/abs/2203.11171)

---

**최종 목표**: 완전자율 AI Agent 달성 (2025년 Q3)  
**핵심 가치**: 인간의 창의력 + AI의 자동화 능력 = 초인적 생산성 🚀
