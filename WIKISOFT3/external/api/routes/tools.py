"""
개별 Tool API 엔드포인트
Windmill 등 외부 워크플로우에서 각 도구를 독립적으로 호출 가능
"""
import json
from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from internal.agent.tool_registry import get_registry
from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.utils.security import validate_upload_file
from internal.calculators.ifrs_calculator import calculate_ifrs

router = APIRouter(prefix="/tools", tags=["tools"])


# ============================================================
# 공통 응답 모델
# ============================================================
class ToolResponse(BaseModel):
    success: bool
    tool: str
    result: Any
    error: Optional[str] = None


# ============================================================
# 1. 명부 파싱
# ============================================================
@router.post("/parse")
async def parse_roster(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    max_rows: Optional[int] = Form(None)
) -> ToolResponse:
    """
    Excel/CSV 파일을 파싱하여 헤더와 행 데이터 추출.
    
    Returns:
        - headers: 컬럼 헤더 리스트
        - rows: 데이터 행 리스트
        - row_count: 총 행 수
    """
    try:
        file_bytes, filename = await validate_upload_file(file)
        registry = get_registry()
        
        kwargs = {"file_bytes": file_bytes}
        if sheet_name:
            kwargs["sheet_name"] = sheet_name
        if max_rows:
            kwargs["max_rows"] = max_rows
        
        result = registry.call_tool("parse_roster", **kwargs)
        
        return ToolResponse(
            success=True,
            tool="parse_roster",
            result={
                "headers": result.get("headers", []),
                "rows": result.get("rows", []),
                "row_count": len(result.get("rows", []))
            }
        )
    except Exception as e:
        return ToolResponse(success=False, tool="parse_roster", result=None, error=str(e))


# ============================================================
# 2. 헤더 매칭
# ============================================================
class MatchRequest(BaseModel):
    headers: List[str]
    sheet_type: str = "재직자"


@router.post("/match")
async def match_headers(request: MatchRequest) -> ToolResponse:
    """
    고객 헤더를 표준 스키마에 매칭.
    
    Input:
        - headers: 원본 헤더 리스트
        - sheet_type: 시트 유형 (재직자/퇴직자)
    
    Returns:
        - matches: 매칭 결과 리스트 [{source, target, confidence, ...}]
        - used_ai: AI 사용 여부
    """
    try:
        registry = get_registry()
        
        # parse_roster 결과 형태로 변환
        parsed = {"headers": request.headers, "rows": []}
        
        result = registry.call_tool(
            "match_headers",
            parsed=parsed,
            sheet_type=request.sheet_type
        )
        
        return ToolResponse(success=True, tool="match_headers", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="match_headers", result=None, error=str(e))


# ============================================================
# 3. 검증
# ============================================================
class ValidateRequest(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    matches: List[Dict[str, Any]]
    diagnostic_answers: Optional[Dict[str, Any]] = None


@router.post("/validate")
async def validate_data(request: ValidateRequest) -> ToolResponse:
    """
    파싱/매칭 결과에 대해 유효성 검사 수행.
    
    Input:
        - headers: 헤더 리스트
        - rows: 데이터 행 리스트
        - matches: 매칭 결과
        - diagnostic_answers: 진단 질문 답변 (선택)
    
    Returns:
        - passed: 검증 통과 여부
        - warnings: 경고 리스트
        - checks: 세부 검사 결과
    """
    try:
        registry = get_registry()
        
        parsed = {"headers": request.headers, "rows": request.rows}
        matches_dict = {"matches": request.matches}
        
        kwargs = {"parsed": parsed, "matches": matches_dict}
        if request.diagnostic_answers:
            kwargs["diagnostic_answers"] = request.diagnostic_answers
        
        result = registry.call_tool("validate", **kwargs)
        
        return ToolResponse(success=True, tool="validate", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="validate", result=None, error=str(e))


# ============================================================
# 4. 중복 탐지
# ============================================================
class DuplicateRequest(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    matches: List[Dict[str, Any]]


@router.post("/detect-duplicates")
async def detect_duplicates(request: DuplicateRequest) -> ToolResponse:
    """
    중복 행 탐지 (완전 일치 / 유사 / 의심).
    
    Returns:
        - has_duplicates: 중복 존재 여부
        - exact_duplicates: 완전 일치 중복
        - similar_duplicates: 유사 중복
        - suspicious_duplicates: 의심 중복
    """
    try:
        registry = get_registry()
        
        df = pd.DataFrame(request.rows, columns=request.headers)
        
        result = registry.call_tool(
            "detect_duplicates",
            df=df,
            headers=request.headers,
            matches=request.matches
        )
        
        return ToolResponse(success=True, tool="detect_duplicates", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="detect_duplicates", result=None, error=str(e))


# ============================================================
# 5. 리포트 생성
# ============================================================
class ReportRequest(BaseModel):
    validation: Dict[str, Any]


@router.post("/report")
async def generate_report(request: ReportRequest) -> ToolResponse:
    """
    검증 결과로부터 리포트 생성.
    
    Input:
        - validation: 검증 결과 객체
    
    Returns:
        - summary: 요약 정보
        - details: 상세 내용
    """
    try:
        registry = get_registry()
        
        result = registry.call_tool("generate_report", validation=request.validation)
        
        return ToolResponse(success=True, tool="generate_report", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="generate_report", result=None, error=str(e))


# ============================================================
# 6. 신뢰도/이상치 분석
# ============================================================
class ConfidenceRequest(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    matches: List[Dict[str, Any]]
    validation: Dict[str, Any]


@router.post("/analyze-confidence")
async def analyze_confidence(request: ConfidenceRequest) -> ToolResponse:
    """
    신뢰도 점수 및 이상치 분석.
    
    Returns:
        - confidence: 신뢰도 점수 및 요인
        - anomalies: 이상치 목록
        - auto_approve: 자동 승인 가능 여부
    """
    try:
        parsed = {"headers": request.headers, "rows": request.rows}
        matches_dict = {"matches": request.matches}
        
        confidence = estimate_confidence(parsed, matches_dict, request.validation)
        anomalies = detect_anomalies(parsed, matches_dict, request.validation)
        
        # 자동 승인 기준: 신뢰도 90% 이상, 에러 없음
        auto_approve = (
            confidence.get("score", 0) >= 0.9 and
            not any(a.get("severity") == "error" for a in anomalies.get("anomalies", []))
        )
        
        return ToolResponse(
            success=True,
            tool="analyze_confidence",
            result={
                "confidence": confidence,
                "anomalies": anomalies,
                "auto_approve": auto_approve
            }
        )
    except Exception as e:
        return ToolResponse(success=False, tool="analyze_confidence", result=None, error=str(e))


# ============================================================
# 7. 파이프라인 (전체 한번에 - 기존 auto-validate와 동일)
# ============================================================
@router.post("/pipeline")
async def run_pipeline(
    file: UploadFile = File(...),
    sheet_type: str = Form("재직자"),
    chatbot_answers: Optional[str] = Form(None)
) -> ToolResponse:
    """
    전체 파이프라인 실행: 파싱 → 매칭 → 검증 → 분석.
    기존 /api/auto-validate와 동일하지만 Tool 형태로 반환.
    
    Returns:
        - parsed: 파싱 결과
        - matches: 매칭 결과
        - validation: 검증 결과
        - confidence: 신뢰도
        - anomalies: 이상치
        - auto_approve: 자동 승인 가능 여부
    """
    try:
        file_bytes, filename = await validate_upload_file(file)
        registry = get_registry()
        
        # 1. 파싱
        parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)
        
        # 2. 매칭
        matches = registry.call_tool("match_headers", parsed=parsed, sheet_type=sheet_type)
        
        # 3. 진단 답변 파싱
        diagnostic_answers = {}
        if chatbot_answers:
            try:
                diagnostic_answers = json.loads(chatbot_answers)
            except json.JSONDecodeError:
                pass
        
        # 4. 검증
        validation = registry.call_tool(
            "validate",
            parsed=parsed,
            matches=matches,
            diagnostic_answers=diagnostic_answers
        )
        
        # 5. 신뢰도/이상치
        confidence = estimate_confidence(parsed, matches, validation)
        anomalies = detect_anomalies(parsed, matches, validation)
        
        # 6. 중복 탐지
        df = pd.DataFrame(parsed.get("rows", []), columns=parsed.get("headers", []))
        duplicates = registry.call_tool(
            "detect_duplicates",
            df=df,
            headers=parsed.get("headers", []),
            matches=matches.get("matches", [])
        )
        
        # 자동 승인 판단
        auto_approve = (
            confidence.get("score", 0) >= 0.9 and
            not any(a.get("severity") == "error" for a in anomalies.get("anomalies", []))
        )
        
        return ToolResponse(
            success=True,
            tool="pipeline",
            result={
                "parsed": {
                    "headers": parsed.get("headers", []),
                    "row_count": len(parsed.get("rows", []))
                },
                "matches": matches,
                "validation": validation,
                "confidence": confidence,
                "anomalies": anomalies,
                "duplicates": duplicates,
                "auto_approve": auto_approve
            }
        )
    except Exception as e:
        return ToolResponse(success=False, tool="pipeline", result=None, error=str(e))


# ============================================================
# 9. IFRS 1019 퇴직급여 부채 계산
# ============================================================
class IFRSRequest(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    matches: List[Dict[str, Any]]
    assumptions: Optional[Dict[str, Any]] = None


class IFRSAssumptions(BaseModel):
    """계리적 가정"""
    discount_rate: float = 0.045          # 할인율 (AA급 회사채 수익률)
    salary_increase_rate: float = 0.03    # 임금상승률
    turnover_rate: float = 0.05           # 이직률
    retirement_age: int = 60              # 정년
    benefit_rate: float = 1.0             # 퇴직급여 지급률


@router.post("/ifrs-calculate")
async def ifrs_calculate(request: IFRSRequest) -> ToolResponse:
    """
    IFRS 1019 퇴직급여 부채 계산 (PUC 방식)
    
    Input:
        - headers: 헤더 리스트
        - rows: 데이터 행 (검증된 명부)
        - matches: 헤더 매칭 결과
        - assumptions: 계리적 가정 (선택)
            - discount_rate: 할인율 (기본 4.5%)
            - salary_increase_rate: 임금상승률 (기본 3%)
            - turnover_rate: 이직률 (기본 5%)
            - retirement_age: 정년 (기본 60세)
            - benefit_rate: 지급률 (기본 1.0)
    
    Returns:
        - summary: 전체 합계 (total_dbo, total_csc, total_interest_cost)
        - employees: 개인별 계산 결과
        - assumptions: 적용된 가정
    """
    try:
        result = calculate_ifrs(
            headers=request.headers,
            rows=request.rows,
            matches=request.matches,
            assumptions=request.assumptions
        )
        
        if not result.get("success"):
            return ToolResponse(
                success=False,
                tool="ifrs_calculate",
                result=None,
                error=result.get("error", "IFRS 계산 실패")
            )
        
        return ToolResponse(success=True, tool="ifrs_calculate", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="ifrs_calculate", result=None, error=str(e))


@router.post("/ifrs-calculate-file")
async def ifrs_calculate_from_file(
    file: UploadFile = File(...),
    sheet_type: str = Form("재직자"),
    discount_rate: float = Form(0.045),
    salary_increase_rate: float = Form(0.03),
    turnover_rate: float = Form(0.05),
    retirement_age: int = Form(60)
) -> ToolResponse:
    """
    파일에서 직접 IFRS 계산 (파싱 + 매칭 + IFRS 계산 한번에)
    
    Input:
        - file: Excel 명부 파일
        - sheet_type: 시트 유형 (재직자/퇴직자)
        - discount_rate: 할인율
        - salary_increase_rate: 임금상승률
        - turnover_rate: 이직률
        - retirement_age: 정년
    
    Returns:
        - summary: 전체 합계
        - employees: 개인별 계산 결과
    """
    try:
        file_bytes, filename = await validate_upload_file(file)
        registry = get_registry()
        
        # 1. 파싱
        parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)
        
        # 2. 매칭
        matches = registry.call_tool("match_headers", parsed=parsed, sheet_type=sheet_type)
        
        # 3. IFRS 계산
        assumptions = {
            "discount_rate": discount_rate,
            "salary_increase_rate": salary_increase_rate,
            "turnover_rate": turnover_rate,
            "retirement_age": retirement_age,
        }
        
        result = calculate_ifrs(
            headers=parsed.get("headers", []),
            rows=parsed.get("rows", []),
            matches=matches.get("matches", []),
            assumptions=assumptions
        )
        
        if not result.get("success"):
            return ToolResponse(
                success=False,
                tool="ifrs_calculate_file",
                result=None,
                error=result.get("error", "IFRS 계산 실패")
            )
        
        # 파싱/매칭 정보도 포함
        result["parsed_summary"] = {
            "headers": parsed.get("headers", []),
            "row_count": len(parsed.get("rows", []))
        }
        result["matches"] = matches
        
        return ToolResponse(success=True, tool="ifrs_calculate_file", result=result)
    except Exception as e:
        return ToolResponse(success=False, tool="ifrs_calculate_file", result=None, error=str(e))


# ============================================================
# 10. 도구 목록 조회
# ============================================================
@router.get("/list")
async def list_tools() -> Dict[str, Any]:
    """사용 가능한 Tool 목록 조회."""
    registry = get_registry()
    
    api_tools = [
        {"name": "parse", "method": "POST", "path": "/api/tools/parse", "description": "Excel/CSV 파일 파싱"},
        {"name": "match", "method": "POST", "path": "/api/tools/match", "description": "헤더 매칭"},
        {"name": "validate", "method": "POST", "path": "/api/tools/validate", "description": "데이터 검증"},
        {"name": "detect-duplicates", "method": "POST", "path": "/api/tools/detect-duplicates", "description": "중복 탐지"},
        {"name": "report", "method": "POST", "path": "/api/tools/report", "description": "리포트 생성"},
        {"name": "analyze-confidence", "method": "POST", "path": "/api/tools/analyze-confidence", "description": "신뢰도/이상치 분석"},
        {"name": "pipeline", "method": "POST", "path": "/api/tools/pipeline", "description": "전체 파이프라인"},
        {"name": "ifrs-calculate", "method": "POST", "path": "/api/tools/ifrs-calculate", "description": "IFRS 1019 퇴직급여 부채 계산"},
        {"name": "ifrs-calculate-file", "method": "POST", "path": "/api/tools/ifrs-calculate-file", "description": "파일에서 직접 IFRS 계산"},
    ]
    
    internal_tools = registry.list_tools()
    
    return {
        "api_tools": api_tools,
        "internal_tools": internal_tools
    }
