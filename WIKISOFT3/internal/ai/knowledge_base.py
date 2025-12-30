"""
Knowledge Base: 시스템 문서를 에이전트에 제공하는 간단한 RAG
"""
import os
from typing import Optional

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
- 필수 헤더: 이름, 생년월일, 입사일, 기준급여, 근속연수 등
"""


def get_system_context(query: Optional[str] = None) -> str:
    """시스템 지식 반환 (현재는 전체, 나중에 쿼리별 필터링 가능)"""
    return SYSTEM_KNOWLEDGE.strip()


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
