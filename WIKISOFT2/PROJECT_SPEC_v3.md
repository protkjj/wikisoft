# 📋 WIKISOFT2 기술 명세서 (Agent-Ready)

**버전**: 2.1 + 3.0 로드맵  
**최종 업데이트**: 2025-12-26  
**상태**: Phase 2.1 완료 → Phase 3 설계 중

---

## 📊 시스템 아키텍처

### 레이어 구조

```
┌─────────────────────────────────────┐
│   API Layer (FastAPI)               │  🔴 현재: main.py (모놀리식)
│                                     │  🟢 미래: routes/ (분산)
├─────────────────────────────────────┤
│   Agent Layer (ReACT Loop)          │  🆕 자동 의사결정
│   - Decision Engine                 │  🆕 신뢰도 기반 선택
│   - Confidence Scorer               │  🆕 도구 자동 선택
├─────────────────────────────────────┤
│   Tool Registry                     │  🆕 도구 중앙 관리
│   ├─ Parser Tools                   │
│   ├─ Validator Tools                │
│   ├─ Analyzer Tools                 │
│   └─ Corrector Tools                │
├─────────────────────────────────────┤
│   Memory Layer                      │  🆕 학습 및 기억
│   ├─ Redis (단기)                   │
│   ├─ Chroma (벡터 DB)               │
│   └─ PostgreSQL (감사 로그)          │
├─────────────────────────────────────┤
│   Core Processing Layer             │  ✅ 현재 구현
│   ├─ Excel Parser                   │
│   ├─ Validator                      │
│   ├─ Anomaly Detector               │
│   └─ Report Generator               │
├─────────────────────────────────────┤
│   Data Layer                        │  📁 파일 저장소
│   └─ Excel Files                    │
└─────────────────────────────────────┘
```

---

## 🔌 API 명세

### 현재 엔드포인트 (v2.1)

#### 1. Health Check
```http
GET /health

Response (200):
{
  "status": "healthy" | "degraded" | "unhealthy",
  "timestamp": "2025-12-26T00:38:27.654109",
  "version": "2.1",
  "checks": {
    "api": "ok",
    "sessions": "0/50",
    "openai_api": "configured"
  }
}
```

#### 2. 진단 질문 조회
```http
GET /diagnostic-questions
Authorization: Bearer <TOKEN>

Response (200):
{
  "questions": [
    {
      "id": "q1",
      "type": "choice",
      "category": "data_quality",
      "question": "사외적립자산...",
      "choices": ["예", "아니오"],
      "unit": null,
      "requires_validation": false
    }
  ],
  "summary": {
    "total": 24,
    "categories": {
      "data_quality": 14,
      "headcount_aggregates": 6,
      "amount_aggregates": 4
    }
  }
}
```

#### 3. 명부 검증 & Layer 2
```http
POST /validate-with-roster
Authorization: Bearer <TOKEN>
Content-Type: multipart/form-data

Body:
- file: manifest.xlsx (binary)
- chatbot_answers: {"q21": 17, "q22": 664, ...} (JSON string)

Response (200):
{
  "validation": {
    "status": "passed" | "warnings" | "failed",
    "total_checks": 8,
    "passed": 6,
    "warnings": [
      {
        "question_id": "q21",
        "severity": "high",
        "message": "명부에서 17명이지만 20명으로 입력",
        "user_input": 20,
        "calculated": 17,
        "diff_percent": 17.6
      }
    ]
  },
  "calculated_aggregates": {
    "counts_I26_I39": [17.0, 664.0, 69.0, ...],
    "sums_I40_I51": [6789774140.0, ...]
  },
  "parsing_warnings": [...],
  "session_id": "abc-123-def",
  "message": "✅ 검증 완료"
}
```

#### 4. Excel 생성
```http
POST /generate-with-validation
Authorization: Bearer <TOKEN>
Content-Type: application/x-www-form-urlencoded

Body:
- session_id: abc-123-def
- company_name: 세라젬
- phone: 02-1234-5678
- email: hr@example.com
- 작성기준일: 20251226

Response (200):
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="퇴직급여채무_세라젬_20251226.xlsx"

[Binary Excel File]
```

---

### 미래 엔드포인트 (v3.0+)

#### 5. 완전자율 검증 (🆕)
```http
POST /auto-validate
Authorization: Bearer <TOKEN>
Content-Type: multipart/form-data

Body:
- file: manifest.xlsx (파일만 필요!)
- confidence_threshold: 0.8 (신뢰도 임계값, 선택)
- mode: "sync" | "async" (처리 방식, 선택)

Response (200):
{
  "status": "success" | "needs_review" | "failed",
  "session_id": "agent-abc-123",
  "confidence": 0.95,
  "processing_time_seconds": 120,
  
  "decisions": [
    {
      "decision_id": "d1",
      "type": "auto_fix",
      "field": "employee_count",
      "from": 20,
      "to": 17,
      "confidence": 0.98,
      "reason": "Manifest calculation shows 17, correcting..."
    }
  ],
  
  "human_inputs": [
    {
      "question_id": "h1",
      "question": "급여 분포가 비정상입니다. 조치 방법은?",
      "user_response": "자동 수정",
      "confidence": 0.72
    }
  ],
  
  "data": {
    "original": {...},
    "corrected": {...}
  },
  
  "report": "<html>...</html>"
}
```

#### 6. 배치 처리 (🆕)
```http
POST /batch-validate
Authorization: Bearer <TOKEN>
Content-Type: multipart/form-data

Body:
- files: [file1.xlsx, file2.xlsx, ..., file100.xlsx]
- mode: "async"
- confidence_threshold: 0.8

Response (202 Accepted):
{
  "job_id": "job-2025-12-26-001",
  "status": "processing",
  "total_files": 100,
  "processed": 15,
  "progress_percent": 15,
  
  "webhook_url": "https://yourserver.com/callback/job-xxx",
  
  "check_status_url": "GET /batch-status/job-2025-12-26-001"
}
```

#### 7. Agent 상태 조회 (🆕)
```http
GET /agent/{session_id}
Authorization: Bearer <TOKEN>

Response (200):
{
  "session_id": "agent-abc-123",
  "state": "thinking" | "deciding" | "waiting_human" | "complete",
  "progress": 0.75,
  
  "current_thought": "직원 인원 이상치가 5%인데, 신뢰도가 높으니 자동 수정하겠습니다",
  
  "next_action": {
    "type": "ask_human",
    "question": "급여 분포가 정상 범위 밖입니다. 어떻게 하시겠어요?",
    "options": [
      "자동 수정 (신뢰도 72%)",
      "수동 검토",
      "보고서에만 기재"
    ]
  },
  
  "decisions_so_far": 5,
  "human_inputs_needed": 1
}
```

---

## 🛠️ Tool Registry 명세

### 도구 정의

```python
# Tool은 다음 인터페이스를 구현
class Tool:
    name: str                    # "parse_excel"
    description: str             # 설명 (LLM 프롬프트용)
    inputs: Dict[str, InputSpec] # 입력 정의
    outputs: Dict[str, OutputSpec] # 출력 정의
    cost: Dict[str, float]       # 비용 (시간, 토큰)
    error_handling: str          # "retry" | "fallback" | "raise"
    
    async def execute(self, **kwargs) -> Dict: pass
```

### 기본 도구들

#### Tool 1: ParseExcelTool
```python
{
  "name": "parse_excel",
  "description": "Excel 파일 파싱 및 기초 정보 수집",
  "inputs": {
    "file_path": "string (required)",
    "sheet_names": "list[string] (optional)"
  },
  "outputs": {
    "dataframe": "pandas.DataFrame",
    "metadata": {
      "sheets": ["재직자", "퇴직자", "추가"],
      "row_count": 753,
      "columns": ["사원번호", "이름", ...]
    }
  },
  "cost": {
    "time_seconds": 2,
    "tokens": 0
  }
}
```

#### Tool 2: ValidateDataTool
```python
{
  "name": "validate_data",
  "description": "데이터 품질 검증 (누락값, 이상치, 규칙 위반)",
  "inputs": {
    "dataframe": "pandas.DataFrame (required)",
    "validation_rules": "list[Rule] (optional)"
  },
  "outputs": {
    "violations": [
      {
        "row": 5,
        "column": "생년월일",
        "violation_type": "invalid_date",
        "value": "1950-02-30",
        "severity": "error"
      }
    ],
    "statistics": {
      "total_cells": 10000,
      "invalid_cells": 15,
      "missing_cells": 3,
      "anomaly_score": 0.18
    }
  },
  "cost": {
    "time_seconds": 3,
    "tokens": 1000
  }
}
```

#### Tool 3: AnomalyDetectorTool
```python
{
  "name": "detect_anomalies",
  "description": "통계 기반 이상치 탐지 (IQR, Z-score)",
  "inputs": {
    "dataframe": "pandas.DataFrame (required)",
    "columns": "list[string] (optional, 지정된 컬럼만)"
  },
  "outputs": {
    "anomalies": [
      {
        "column": "기준급여",
        "row": 123,
        "value": 50000000,
        "expected_range": [2000000, 8000000],
        "z_score": 3.5,
        "severity": "high"
      }
    ]
  },
  "cost": {
    "time_seconds": 2,
    "tokens": 500
  }
}
```

#### Tool 4: AutoCorrectTool
```python
{
  "name": "auto_correct",
  "description": "자동 수정 (신뢰도 기반 전략)",
  "inputs": {
    "dataframe": "pandas.DataFrame (required)",
    "violations": "list[Violation] (required)",
    "strategy": "optimistic" | "conservative" (optional)"
  },
  "outputs": {
    "corrected_dataframe": "pandas.DataFrame",
    "corrections": [
      {
        "row": 5,
        "column": "생년월일",
        "original": "1950-02-30",
        "corrected": "1950-02-28",
        "method": "date_normalization",
        "confidence": 0.95
      }
    ]
  },
  "cost": {
    "time_seconds": 5,
    "tokens": 2000
  }
}
```

#### Tool 5: ConfidenceEstimatorTool
```python
{
  "name": "estimate_confidence",
  "description": "수정 결과의 신뢰도 평가",
  "inputs": {
    "original_data": "pandas.DataFrame (required)",
    "corrected_data": "pandas.DataFrame (required)",
    "corrections": "list[Correction] (required)"
  },
  "outputs": {
    "overall_confidence": 0.92,
    "breakdown": {
      "data_quality": 0.95,
      "rule_match": 0.90,
      "fix_stability": 0.88,
      "case_similarity": 0.93
    },
    "recommendation": "AUTO_COMPLETE"
  },
  "cost": {
    "time_seconds": 1,
    "tokens": 300
  }
}
```

#### Tool 6: GenerateReportTool
```python
{
  "name": "generate_report",
  "description": "최종 검증 리포트 생성 (HTML)",
  "inputs": {
    "dataframe": "pandas.DataFrame (required)",
    "decisions": "list[Decision] (required)",
    "human_inputs": "list[HumanInput] (optional)"
  },
  "outputs": {
    "report_html": "<html>...</html>",
    "report_json": {...},
    "summary": {
      "total_issues": 15,
      "auto_fixed": 12,
      "needs_review": 3
    }
  },
  "cost": {
    "time_seconds": 2,
    "tokens": 500
  }
}
```

---

## 🧠 Decision Engine 명세

### 신뢰도 계산 알고리즘

```python
class ConfidenceCalculator:
    def calculate(state: Dict) -> float:
        """
        종합 신뢰도 (0.0 ~ 1.0)
        """
        
        # 1. 데이터 품질 점수 (30%)
        data_quality = 1.0 - (violations_count / total_cells)
        
        # 2. 검증 규칙 적중도 (25%)
        rule_match = passed_rules / total_rules
        
        # 3. 자동수정 안정성 (20%)
        # → 얼마나 많은 사례에서 이 수정이 성공했는가?
        fix_stability = self.lookup_past_successes(correction_type)
        
        # 4. 과거 사례 유사도 (15%)
        # → 유사한 파일을 본 적 있는가?
        case_similarity = self.find_similar_cases(current_data)
        
        # 5. LLM 신뢰도 (10%)
        model_confidence = llm_output.confidence_score
        
        overall = (
            0.30 * data_quality +
            0.25 * rule_match +
            0.20 * fix_stability +
            0.15 * case_similarity +
            0.10 * model_confidence
        )
        
        return min(1.0, max(0.0, overall))
```

### 의사결정 테이블

```
신뢰도        →  추천 액션           상태               사람 개입
─────────────────────────────────────────────────────
≥ 0.95       →  AUTO_COMPLETE      ✅ 완료             0%
0.80 ~ 0.95  →  AUTO_CORRECT       ✅ 수정 + 알림      ~5%
0.70 ~ 0.80  →  AUTO_WITH_REVIEW   🟡 수정 + 검토      ~15%
0.50 ~ 0.70  →  ASK_HUMAN          ❓ 사람 결정        ~80%
< 0.50       →  MANUAL_REVIEW      🔴 수동 검토        ~100%
```

---

## 💾 데이터 모델

### AgentState
```python
@dataclass
class AgentState:
    session_id: str
    file_path: str
    
    # 현재 상태
    step: int = 0
    status: str = "thinking"  # thinking, deciding, waiting, complete
    
    # 데이터
    original_data: pd.DataFrame = None
    current_data: pd.DataFrame = None
    
    # 의사결정 이력
    thoughts: List[str] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    observations: List[Dict] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    
    # 신뢰도
    confidence: float = 0.0
    
    # 사람 개입
    human_inputs: List[Dict] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        return self.status == "complete"
```

### Decision
```python
@dataclass
class Decision:
    decision_id: str
    type: str  # "auto_fix", "ask_human", "complete"
    field: str
    from_value: Any
    to_value: Any
    confidence: float
    reason: str
    timestamp: datetime
```

---

## 🔐 보안 명세

### API 인증
```
모든 엔드포인트 (except /health):
Authorization: Bearer <API_TOKEN>

Token Format:
- Bearer token (RFC 6750)
- 고정 길이 32자 이상
- 환경변수에서 로드

검증:
1. Authorization 헤더 존재 확인
2. Bearer 스킴 확인
3. 토큰 값 비교
```

### 파일 검증
```
1. 확장자 검증: .xls, .xlsx만
2. MIME 타입: application/vnd.ms-excel, ...
3. 파일 크기: 최대 50MB
4. Magic bytes: XLS (0xD0CF), XLSX (0x504B)
```

### 데이터 보호
```
- 개인정보 마스킹 (로그에서)
- 세션 타임아웃: 120분
- 감사 로그: 모든 의사결정 기록
- HTTPS: 프로덕션 필수
```

---

## 📈 성능 지표

### 처리 성능
```
현재 (v2.1):
- 파일당 시간: 30-60분
- 자동화율: 0% (사람이 모든 질문에 답변)
- 처리량: ~10파일/일

미래 (v3.0):
- 파일당 시간: 5-10분
- 자동화율: 85-90%
- 처리량: ~100파일/일

목표 (v4.0):
- 파일당 시간: 1분
- 자동화율: 95%+
- 처리량: 1000+파일/일
```

### API 응답 시간
```
/health: <100ms
/diagnostic-questions: <500ms
/auto-validate (1000행): 2-5초
/batch-validate (100파일): 비동기 처리
```

---

## 🧪 테스트 전략

### Unit Tests
```
- Tool Registry: 각 도구별 테스트
- Confidence Scorer: 신뢰도 계산 정확도
- Decision Engine: 의사결정 로직
- Memory: 패턴 저장/조회
```

### Integration Tests
```
- ReACT Loop: 전체 흐름
- Tool 조합: 여러 도구를 순차적으로 호출
- Human-in-the-loop: 사람 입력 처리
```

### E2E Tests
```
- 실제 Excel 파일로 테스트
- 신뢰도 기준값 검증
- 성능 벤치마크
```

---

## 🔄 배포 전략

### Staging
```
1. 로컬에서 테스트
2. Docker 컨테이너로 빌드
3. Staging 환경에 배포
4. 성능 테스트 (1000파일)
5. 메모리 누수 확인
```

### Production
```
1. 카나리 배포 (10% 트래픽)
2. 모니터링 (에러율, 처리 시간)
3. 롤백 계획 준비
4. 점진적 확대 (100% 트래픽)
```

---

**최종 목표**: 완전자율 AI Agent 구현 (v4.0, 2025년 Q3)
