"""
Knowledge Base: 시스템 문서를 에이전트에 제공하는 간단한 RAG
"""
import os
import json
from typing import Optional, List, Dict
from datetime import datetime

# 시스템 문서 요약 (수동 큐레이션)
SYSTEM_KNOWLEDGE = """
=== WIKISOFT3 시스템 개요 ===
목적: HR/재무 엑셀 자동 검증 시스템. 재직자 명부를 받아 파싱·매칭·검증·리포트 생성.
자동화율 목표: 85% 이상 (현재 ~30%)
처리 시간 목표: 5분/파일 (현재 30분)

=== 핵심 철학 ===
1. 자연스러운 매칭이 핵심 - AI는 가속기, 폴백이 기본
2. UX가 기술보다 중요 - 질문 최소화, 뒤로가기, 버튼 위치 고정
3. 경고는 차단이 아니라 안내 - 투명성 확보 목적
4. 신뢰도 기반 의사결정 - 95% 이상만 자동, 나머지는 확인 요청

=== 아키텍처 ===
- API Layer: FastAPI (포트 8003)
- Agent Layer: Tool Registry, Confidence Scorer, Decision Engine
- Core Tools: Parser(Excel), AI Matcher(GPT-4o), Validator(L1/L2), Report Generator
- Queue Layer: Redis/RQ (배치 작업용)
- Frontend: React + Vite (포트 3003)

=== 주요 엔드포인트 ===
- GET /api/health - 시스템 상태
- GET /api/diagnostic-questions - 13개 진단 질문
- POST /api/auto-validate - 파일 검증
- POST /api/batch-validate - 배치 검증
- POST /api/agent/ask - AI 에이전트 대화

=== 진단 질문 (13개) ===
재직자 명부 검증을 위한 정책/데이터 품질 확인 질문:
- 사외적립자산, 정년, 임금피크제, 기타장기종업원급여
- 연봉제/호봉제, 채권등급, 1년미만재직자, 기준급여
- 재직자명부 퇴사자제외, 중간정산
- 임원/일반직원/계약직 인원 집계 (누락/중복 검증용)

=== 검증 프로세스 ===
1. 파싱: Excel/CSV → 표준 스키마
2. 매칭: 고객 헤더 → 표준 컬럼 (AI + 폴백)
3. 검증: Layer1(형식) + Layer2(교차검증)
4. 신뢰도 계산: 매칭 신뢰도 + 에러율
5. 리포트 생성: 오류/경고/요약

=== 신뢰도 임계값 ===
- 95% 이상: 자동 통과
- 85-95%: 경고 + 수동 확인 권장
- 85% 미만: 수동 매핑 필요

=== 지원 파일 형식 ===
- Excel: .xlsx, .xls
- 최대 행: 100,000행
- 필수 헤더: 사원번호, 생년월일, 입사일, 성별, 종업원구분, 기준급여 등
"""

# ============================================================
# 퇴직급여채무 검증 규칙 (Error Check 기반)
# ============================================================
ERROR_CHECK_RULES = """
=== 퇴직급여채무 Error Check 규칙 ===

## 1. 값 유효성 검사
- 퇴직금추계액 < 0 → 오류 (음수 불가)
- 퇴직금추계액(차년도) < 0 → 오류 (음수 불가)
- 기준급여 < 1,900,000원 → 경고 (최저임금 미달 가능성)
- 사원번호 = blank → 오류 (필수 필드)

## 2. 날짜/연령 검사
- 입사연령 < 17세 → 오류 (아동노동법 위반)
- 입사연령 > 70세 → 경고 (이례적 고령 입사)
- 입사일 < 생년월일 → 오류 (시간상 불가능)
- 시산일 <= 입사일 → 오류 (평가일 이전 입사 필요)

## 3. 날짜 형식 검사
- 생년월일: 월>12 or 일>31 → 오류 (잘못된 날짜)
- 입사일: 월>12 or 일>31 → 오류 (잘못된 날짜)

## 4. 교차 검증 (전년도 vs 당년도)
- 입사일 변경 → 경고 (입사일은 변경되지 않아야 함)
- 생년월일 변경 → 오류 (생년월일은 절대 변경 불가)
- 성별 변경 → 오류 (성별 변경은 이례적)

## 5. 인원 대사
- 당년도 재직자 = 전년도 재직자 + 신입사원 - 퇴직자
- 인원수 불일치 시 → 오류

## 6. 기타 주의사항
- 명부에 이름 포함 금지 (개인정보 보호)
- 입사일에 연도 4자리 포함 필수 (예: 19xx, 20xx)
- 퇴직자 중 신입사원 수 확인 (당년 입사 후 퇴직 케이스)

## 7. 계산 방식별 주의
- 일할: 일 단위 정밀 계산
- 월절상: 월 단위 올림
- 6개월절상: 6개월 단위 올림  
- 비례/비비례: 퇴직급여 비례배분 방식
"""

# ============================================================
# 학습 데이터셋 관리 (나중에 파인튜닝용)
# ============================================================
TRAINING_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "training_data"
)


def save_training_example(
    input_data: Dict,
    ai_response: Dict,
    human_correction: Optional[Dict] = None,
    is_correct: bool = True,
    category: str = "general"
) -> str:
    """
    AI 응답과 사람의 수정을 학습 데이터로 저장.
    나중에 파인튜닝할 때 사용.
    
    Args:
        input_data: 입력 데이터 (진단 답변, 명부 요약 등)
        ai_response: AI가 생성한 응답
        human_correction: 사람이 수정한 내용 (있는 경우)
        is_correct: AI 응답이 맞았는지 여부
        category: 분류 (validation, matching, analysis 등)
    
    Returns:
        저장된 파일 경로
    """
    os.makedirs(TRAINING_DATA_PATH, exist_ok=True)
    
    example = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "input": input_data,
        "ai_response": ai_response,
        "human_correction": human_correction,
        "is_correct": is_correct,
    }
    
    filename = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(TRAINING_DATA_PATH, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
    
    return filepath


def load_training_examples(category: Optional[str] = None) -> List[Dict]:
    """저장된 학습 데이터 로드"""
    if not os.path.exists(TRAINING_DATA_PATH):
        return []
    
    examples = []
    for filename in os.listdir(TRAINING_DATA_PATH):
        if not filename.endswith(".json"):
            continue
        if category and not filename.startswith(category):
            continue
        
        filepath = os.path.join(TRAINING_DATA_PATH, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            examples.append(json.load(f))
    
    return examples


def get_few_shot_examples(category: str, limit: int = 3) -> str:
    """
    Few-shot 프롬프트용 예시 생성.
    올바른 응답 예시만 선택해서 프롬프트에 포함.
    """
    examples = load_training_examples(category)
    correct_examples = [e for e in examples if e.get("is_correct", False)]
    
    # 최신 예시 우선
    correct_examples.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    selected = correct_examples[:limit]
    
    if not selected:
        return ""
    
    result = "=== 참고 예시 ===\n"
    for i, ex in enumerate(selected, 1):
        result += f"\n### 예시 {i}\n"
        result += f"입력: {json.dumps(ex['input'], ensure_ascii=False)}\n"
        if ex.get("human_correction"):
            result += f"정답: {json.dumps(ex['human_correction'], ensure_ascii=False)}\n"
        else:
            result += f"응답: {json.dumps(ex['ai_response'], ensure_ascii=False)}\n"
    
    return result


def get_system_context(query: Optional[str] = None, include_rules: bool = True) -> str:
    """시스템 지식 반환 (Error Check 규칙 포함)"""
    result = SYSTEM_KNOWLEDGE.strip()
    
    if include_rules:
        result += "\n\n" + ERROR_CHECK_RULES.strip()
    
    return result


def get_error_check_rules() -> str:
    """Error Check 규칙만 반환"""
    return ERROR_CHECK_RULES.strip()


def load_document(filename: str) -> str:
    """문서 파일 로드 (ARCHITECTURE.md, PROJECT_SPEC.md 등)"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_path, filename)
    
    if not os.path.exists(file_path):
        return ""
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
