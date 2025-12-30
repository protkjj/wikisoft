from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import uvicorn
import asyncio
from dotenv import load_dotenv
import json
import logging
from uuid import uuid4

# .env 파일 로드
load_dotenv()

from internal.models.session import Session
from internal.processors.validation_layer1 import validate_layer1
from internal.validation.anomaly_detector import AnomalyDetector
from internal.ai.question_builder import build_questions
from internal.utils.masking import mask_error_list
from internal.utils.logging import get_logger
from internal.parsers.ceragem_parser import parse_all as parse_ceragem
from internal.generators.aggregate_calculator import aggregate_from_excel
from internal.generators.sheet_generator import (
    save_sheet_1_2_to_bytes,
    save_sheet_1_2_from_chatbot_to_bytes
)
from internal.processors.validation_layer2 import validate_chatbot_answers
from internal.ai.diagnostic_questions import ALL_QUESTIONS, get_validation_questions

# v2.2: Agent Framework 임포트
from internal.tools.registry import get_registry
from internal.tools.parser import register_parser_tool
from internal.tools.validator import register_validator_tools
from internal.tools.analyzer import register_analyzer_tools
from internal.tools.corrector import register_corrector_tools
from internal.agent.react_loop import ReACTLoop
from internal.agent.confidence import ConfidenceCalculator
from internal.agent.decision_engine import DecisionEngine
from internal.agent.memory import get_memory
from internal.config.schema_config import get_schema_config
from internal.config.prompt_config import get_prompt_config

# ============================================
# 로거 설정 (구조화된 로깅)
# ============================================
logger = get_logger(__name__)

# 구조화된 로거 클래스
class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **context):
        """구조화된 로깅 (JSON)"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": message,
            **context
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False))
    
    def error(self, message: str, exc=None, **context):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": message,
            "exception": str(exc) if exc else None,
            **context
        }
        self.logger.error(json.dumps(log_data, ensure_ascii=False))
    
    def warning(self, message: str, **context):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": "WARNING",
            "message": message,
            **context
        }
        self.logger.warning(json.dumps(log_data, ensure_ascii=False))

structured_logger = StructuredLogger(__name__)

# 환경변수
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", "120"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "100"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
API_TOKEN = os.getenv("API_TOKEN")  # 프로덕션에서는 필수 (개발 환경에서는 None 가능)
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_ROWS = 50000
USE_HTTPS = os.getenv("USE_HTTPS", "false").lower() == "true"
SSL_KEYFILE = os.getenv("SSL_KEYFILE", "key.pem")
SSL_CERTFILE = os.getenv("SSL_CERTFILE", "cert.pem")
ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}
ALLOWED_MIMETYPES = {
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream'  # Excel 파일이 가끔 이 MIME 타입으로 올 수 있음
}

# FastAPI 앱 (OpenAPI Docs 포함)
app = FastAPI(
    title="WIKISOFT2 AI Agent API",
    version="2.2",
    description="HR 매니페스트 자동 검증 시스템 - AI Agent 기반",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"  # OpenAPI Schema
)

# CORS 설정 (명시적 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ============================================
# 에러 응답 모델
# ============================================

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None
    request_id: str = ""

class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    checks: Dict[str, str]

# ============================================
# 전역 에러 핸들러
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    request_id = request.headers.get("x-request-id", str(uuid4())[:8])
    
    structured_logger.error(
        "HTTP Exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": request_id
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 검증 오류"""
    request_id = request.headers.get("x-request-id", str(uuid4())[:8])
    
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    structured_logger.warning(
        "Validation Error",
        request_id=request_id,
        errors=error_details
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "입력 형식이 올바르지 않습니다",
            "details": {"errors": error_details[:5]},  # 첫 5개만
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    request_id = request.headers.get("x-request-id", str(uuid4())[:8])
    
    structured_logger.error(
        "Unhandled Exception",
        request_id=request_id,
        exc=exc,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "시스템 오류가 발생했습니다. 관리자에게 문의하세요.",
            "request_id": request_id
        }
    )

# ============================================
# 세션 관리
# ============================================

# 세션 관리 (인메모리 LRU)
class SessionManager:
    def __init__(self, ttl_minutes=120, max_sessions=100):
        self.sessions: Dict[str, Session] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_sessions = max_sessions
    
    def create_session(self, df: pd.DataFrame, diagnostic_answers: Dict[str, str]) -> Session:
        """새 세션 생성"""
        if len(self.sessions) >= self.max_sessions:
            # 가장 오래된 세션 삭제
            oldest_id = min(self.sessions.keys(), key=lambda k: self.sessions[k].last_accessed)
            del self.sessions[oldest_id]
        
        session = Session.create(df, diagnostic_answers)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """세션 조회"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_access_time()
            
            # TTL 체크
            if datetime.now() - session.created_at > self.ttl:
                del self.sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            
            return session
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session deleted: {session_id}")
            return True
        return False
    
    def cleanup_expired(self):
        """만료된 세션 정리 (백그라운드 태스크에서 호출)"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.created_at > self.ttl
        ]
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Session auto-cleaned: {sid}")

session_manager = SessionManager(SESSION_TTL_MINUTES, MAX_SESSIONS)

# ============================================
# v2.2: Agent Framework 초기화
# ============================================

# Tool Registry 초기화
registry = get_registry()
register_parser_tool(registry)
register_validator_tools(registry)
register_analyzer_tools(registry)
register_corrector_tools(registry)

# Agent 컴포넌트 초기화
react_loop = ReACTLoop(registry=registry, llm_client=None)  # Mock LLM
confidence_calculator = ConfidenceCalculator()
decision_engine = DecisionEngine()

structured_logger.info(
    "Agent Framework Initialized",
    total_tools=len(registry.list()),
    tools=[t.name for t in registry.list()]
)

# ============================================
# 인증 & 파일 검증 함수
# ============================================

def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """
    API 토큰 검증
    
    헤더: Authorization: Bearer YOUR_API_TOKEN
    
    개발 환경 (API_TOKEN 없음): 검증 스킵
    프로덕션 환경 (API_TOKEN 설정): 토큰 검증 필수
    """
    if not API_TOKEN:
        # 개발 환경 (토큰 없음)
        structured_logger.warning("DEV_MODE: API_TOKEN not configured, skipping validation")
        return "dev-token"
    
    # 프로덕션 환경 (토큰 검증)
    if not authorization:
        structured_logger.warning("auth_missing: Authorization header required")
        raise HTTPException(
            status_code=401,
            detail="Authorization 헤더가 필요합니다. 형식: Bearer YOUR_API_TOKEN"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            structured_logger.warning(f"auth_invalid_scheme: {scheme}")
            raise HTTPException(status_code=401, detail="Bearer 토큰 형식이 필요합니다")
        
        if token != API_TOKEN:
            structured_logger.warning("auth_token_mismatch")
            raise HTTPException(status_code=403, detail="API 토큰이 일치하지 않습니다")
        
        return token
    except ValueError:
        structured_logger.warning("auth_malformed")
        raise HTTPException(status_code=401, detail="Authorization 헤더 형식이 올바르지 않습니다")


async def validate_file(file: UploadFile) -> bytes:
    """
    파일 검증: 확장자 + MIME 타입 + 크기 + magic bytes
    
    Returns: 파일 바이너리 콘텐츠
    """
    # 1. 파일명 확장자 체크
    import os as os_module
    file_ext = os_module.path.splitext(file.filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        structured_logger.warning(
            "file_invalid_extension",
            filename=file.filename,
            extension=file_ext
        )
        raise HTTPException(
            status_code=400,
            detail=f"❌ 허용되지 않는 파일 형식: {file_ext} (Excel 파일만 가능: .xls, .xlsx)"
        )
    
    # 2. 파일 콘텐츠 읽기
    content = await file.read()
    
    # 3. 파일 크기 체크
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        structured_logger.warning(
            "file_too_large",
            filename=file.filename,
            size=len(content),
            max_size=MAX_UPLOAD_SIZE_BYTES
        )
        raise HTTPException(
            status_code=413,
            detail=f"❌ 파일이 너무 큼: {len(content) / 1024 / 1024:.1f}MB (최대 50MB)"
        )
    
    # 4. Magic bytes 검증
    if file_ext == '.xls':
        if not content.startswith(b'\xd0\xcf\x11\xe0'):
            structured_logger.warning("file_invalid_xls_format", filename=file.filename)
            raise HTTPException(status_code=400, detail="❌ 유효하지 않은 XLS 파일입니다")
    
    elif file_ext == '.xlsx':
        if not content.startswith(b'PK'):
            structured_logger.warning("file_invalid_xlsx_format", filename=file.filename)
            raise HTTPException(status_code=400, detail="❌ 유효하지 않은 XLSX 파일입니다")
    
    structured_logger.info(
        "file_validated",
        filename=file.filename,
        size=len(content),
        extension=file_ext
    )
    
    return content

# ============================================
# Pydantic 검증 모델
# ============================================

class ChatbotAnswersModel(BaseModel):
    answers: Dict[str, Any]
    
    @validator('answers')
    def validate_answers(cls, v):
        """필수 필드 검증"""
        if not isinstance(v, dict):
            raise ValueError("챗봇 답변은 JSON 객체여야 합니다")
        
        if not v:
            raise ValueError("최소 1개 이상의 답변이 필요합니다")
        
        # 타입 검증 (q21-q25는 숫자)
        for qid in ['q21', 'q22', 'q23', 'q24', 'q25']:
            if qid in v:
                try:
                    float(v[qid])
                except (ValueError, TypeError):
                    raise ValueError(f"{qid}: 숫자만 입력 가능 (현재값: {v[qid]})")
        
        return v

# ============================================
# 백그라운드 정리 태스크
# ============================================


# 백그라운드 정리 태스크
async def cleanup_task():
    """
    주기적으로 만료된 세션을 정리하는 백그라운드 태스크
    앱 시작 후 30분마다 실행 (TTL이 120분이므로 30분 주기면 충분)
    """
    await asyncio.sleep(30)  # 앱 시작 후 30초 대기
    
    while True:
        try:
            session_manager.cleanup_expired()
            logger.info(f"Cleanup task executed. Active sessions: {len(session_manager.sessions)}")
            await asyncio.sleep(1800)  # 30분마다 실행 (1800초)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """앱 시작 시"""
    asyncio.create_task(cleanup_task())
    structured_logger.info(
        "startup",
        version="2.1",
        api_token_configured=bool(API_TOKEN),
        max_sessions=MAX_SESSIONS,
        session_ttl_minutes=SESSION_TTL_MINUTES
    )

# ============================================
# Health Check
# ============================================

@app.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    서버 상태 체크 (Kubernetes/로드밸런서용)
    
    curl http://localhost:8000/health
    """
    checks = {
        "api": "ok",
        "sessions": f"{len(session_manager.sessions)}/{MAX_SESSIONS}",
        "openai_api": "not_configured" if not OPENAI_API_KEY else "configured"
    }
    
    status = "healthy"
    
    # 세션 수 경고
    if len(session_manager.sessions) > MAX_SESSIONS * 0.8:
        checks["sessions_warning"] = "approaching limit"
        status = "degraded"
    
    # OpenAI API 연결성 체크 (선택)
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            # API 연결 테스트는 비싼 작업이므로 스킵
            checks["openai_api"] = "configured"
        except Exception as e:
            checks["openai_api"] = f"error"
            status = "degraded"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.now().isoformat(),
        version="2.1",
        checks=checks
    )

# ============================================
# 라우터

@app.get("/")
def root():
    return {"message": "WIKISOFT2 API running", "version": "1.0"}

# ============================================
# v2.2: 자동 검증 엔드포인트 (ReACT Loop 기반)
# ============================================

class AutoValidateResponse(BaseModel):
    """자동 검증 응답"""
    success: bool
    file_name: str
    react_steps: int
    overall_confidence: float
    decision: Dict[str, Any]
    validation_result: Dict[str, Any]
    execution_time: float


@app.post("/auto-validate", response_model=AutoValidateResponse)
async def auto_validate(
    file: UploadFile = File(...),
    token: str = Depends(verify_token),
    request: Request = None
) -> AutoValidateResponse:
    """
    자동 검증 엔드포인트 (ReACT Loop 기반)
    
    파일만 업로드하면 다음을 자동으로 수행:
    1. ReACT Loop: Tool Registry를 사용한 자동 검증
    2. Confidence 계산: 신뢰도 점수 산출
    3. Decision Engine: 자동 의사결정
    
    curl -X POST -F "file=@test.xlsx" -H "Authorization: Bearer YOUR_TOKEN" \\
         http://localhost:8000/auto-validate
    """
    request_id = request.headers.get("x-request-id", str(uuid4())[:8]) if request else str(uuid4())[:8]
    
    try:
        import time
        start_time = time.time()
        
        structured_logger.info(
            "auto_validate_start",
            request_id=request_id,
            filename=file.filename
        )
        
        # 1. 파일 검증
        content = await validate_file(file)
        
        # 2. 파일 파싱
        try:
            excel_file = pd.ExcelFile(io.BytesIO(content))
            df = pd.read_excel(io.BytesIO(content), sheet_name=0)
        except Exception as e:
            structured_logger.error(
                "auto_validate_parse_error",
                request_id=request_id,
                error=str(e)
            )
            raise HTTPException(status_code=400, detail=f"❌ Excel 파일 파싱 실패: {str(e)}")
        
        # 3. ReACT Loop 실행
        react_result = await react_loop.run(
            file_path=file.filename,
            task="validate",
            max_steps=5,
            confidence_threshold=0.85
        )
        
        if not react_result.get("success"):
            structured_logger.warning(
                "auto_validate_react_failed",
                request_id=request_id,
                error=react_result.get("error")
            )
            raise HTTPException(
                status_code=500,
                detail=f"❌ ReACT Loop 실행 실패: {react_result.get('error')}"
            )
        
        # 4. 신뢰도 계산
        react_state = react_result.get("state", {})
        overall_confidence = react_result.get("result", {}).get("confidence", 0.5)
        
        # Confidence 스코어 계산
        confidence_score = confidence_calculator.calculate(
            action_confidence=0.7,
            tool_confidence=overall_confidence,
            data_quality=0.8,
            result_confidence=0.75
        )
        
        # 5. Decision Engine: 자동 의사결정
        data_sample = {
            "file": file.filename,
            "rows": len(df),
            "columns": len(df.columns)
        }
        
        decision = await decision_engine.decide(
            confidence=confidence_score.overall,
            data=data_sample,
            result={"success": True, "confidence": confidence_score.overall},
            context={"file_path": file.filename}
        )
        
        # 6. 응답 생성
        execution_time = time.time() - start_time
        
        response = AutoValidateResponse(
            success=True,
            file_name=file.filename,
            react_steps=react_result.get("steps", 0),
            overall_confidence=round(confidence_score.overall, 3),
            decision={
                "type": decision.type.value,
                "reason": decision.reason.value,
                "message": decision.message,
                "confidence": decision.confidence,
            },
            validation_result={
                "status": "passed",
                "total_checks": len(react_result.get("state", {}).get("actions", [])),
                "passed_checks": sum(1 for o in react_result.get("state", {}).get("observations", []) if o.get("success")),
                "react_summary": react_result.get("result", {}).get("summary", ""),
            },
            execution_time=round(execution_time, 3)
        )
        
        structured_logger.info(
            "auto_validate_success",
            request_id=request_id,
            filename=file.filename,
            confidence=confidence_score.overall,
            decision=decision.type.value,
            execution_time=execution_time
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error(
            "auto_validate_error",
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"❌ 자동 검증 중 오류: {str(e)}"
        )


@app.post("/parse")
async def parse_only(file: UploadFile = File(...), token: str = Depends(verify_token)):
    """엑셀 파일 파싱만 수행해 세션에 저장하고 요약 반환 (검증/LLM 없음)."""
    try:
        # 타입 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="XLS/XLSX 파일만 지원합니다")
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (50MB 제한)")

        # 파싱 실행
        parsed = parse_ceragem(content)

        # 임시 세션 생성 (진단 답변 없음)
        df_placeholder = pd.DataFrame()
        session = session_manager.create_session(df_placeholder, {})
        session.parsed_data = parsed
        
        # Build detailed response with labeled cells and comparisons
        from internal.parsers.ceragem_parser import CELL_I40_I51_LABELS
        
        # Extract and label I40-I51 cells
        sums_i40_i51 = parsed.get('core_info', {}).get('sums_I40_I51', [])
        labeled_cells = {}
        for i, (cell_addr, label) in enumerate(CELL_I40_I51_LABELS.items()):
            labeled_cells[cell_addr] = {
                'label': label,
                'value': sums_i40_i51[i] if i < len(sums_i40_i51) else None
            }
        
        # Build detailed comparison tables
        detailed_comparisons = []
        
        # Count comparison
        for check in parsed.get('cross_checks', []):
            if check.get('type') == 'compare_counts_core_vs_lists':
                detailed_comparisons.append({
                    'category': '인원수 비교',
                    'core_value': check.get('core_total'),
                    'lists_value': check.get('lists_total'),
                    'difference': check.get('diff'),
                    'status': check.get('status'),
                    'explanation': f"Core 합계: {check.get('core_total', 0):,.0f}명, 명부 합계: {check.get('lists_total', 0):,.0f}명"
                })
            elif check.get('type') == 'compare_amounts_core_vs_lists':
                detailed_comparisons.append({
                    'category': '금액 비교',
                    'core_value': check.get('core_total'),
                    'lists_value': check.get('lists_total'),
                    'difference': check.get('diff'),
                    'status': check.get('status'),
                    'explanation': f"Core 합계: {check.get('core_total', 0):,.0f}원, 명부 합계: {check.get('lists_total', 0):,.0f}원"
                })
        
        # Formula validation summary
        formula_results = []
        for check in parsed.get('cross_checks', []):
            if 'formula_' in check.get('type', ''):
                formula_results.append({
                    'formula': check.get('label', check.get('type')),
                    'lhs': check.get('lhs'),
                    'rhs': check.get('rhs'),
                    'diff': check.get('diff'),
                    'status': check.get('status'),
                    'pass': check.get('status') == 'match'
                })

        return {
            "session_id": session.session_id,
            "message": "파싱 완료",
            "parsed_summary": {
                "active": parsed["active"]["summary"],
                "retired_dc": parsed["retired_dc"]["summary"],
                "additional": parsed["additional"]["summary"],
                "cross_checks": parsed["cross_checks"],
                "core_info": parsed["core_info"],
            },
            "labeled_cells": labeled_cells,
            "detailed_comparisons": detailed_comparisons,
            "formula_validations": formula_results,
            "validation_summary": {
                "total_formulas": len(formula_results),
                "formulas_passed": sum(1 for f in formula_results if f['pass']),
                "formulas_failed": sum(1 for f in formula_results if not f['pass']),
                "cross_check_status": {
                    "total": len(parsed.get('cross_checks', [])),
                    "matches": sum(1 for c in parsed.get('cross_checks', []) if c.get('status') == 'match'),
                    "mismatches": sum(1 for c in parsed.get('cross_checks', []) if c.get('status') == 'mismatch')
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate_sheet_1_2(
    file: UploadFile = File(...),
    company_name: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    작성기준일: str = Form(None),
    token: str = Depends(verify_token)
):
    """
    재직자 명부만으로 (1-2) 기초자료 시트 자동 생성
    
    Parameters:
    - file: 재직자 명부 Excel (CSV/XLS/XLSX)
    - company_name: 회사명 (선택)
    - phone: 전화번호 (선택)
    - email: 이메일 (선택)
    - 작성기준일: YYYYMMDD 형식 (선택, 기본값: 오늘)
    
    Returns:
    - Excel 파일 (다운로드)
    """
    try:
        # 파일 검증
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="Excel 또는 CSV 파일만 지원합니다")
        
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (50MB 제한)")
        
        # 명부에서 집계 계산
        aggregated = aggregate_from_excel(content)
        
        # 회사 정보
        company_info = {}
        if company_name:
            company_info['회사명'] = company_name
        if phone:
            company_info['전화번호'] = phone
        if email:
            company_info['이메일'] = email
        
        # 작성기준일
        if not 작성기준일:
            작성기준일 = datetime.now().strftime('%Y%m%d')
        
        # (1-2) 시트 생성
        excel_bytes = save_sheet_1_2_to_bytes(aggregated, company_info, 작성기준일)
        
        # 파일 응답
        from fastapi.responses import Response
        filename = f"기초자료_퇴직급여_{작성기준일}.xlsx"
        
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate(
    file: UploadFile = File(...),
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(...),
    q5: str = Form(...),
    q6: str = Form(...),
    q7: str = Form(...),
    q8: str = Form(...),
    q9: str = Form(...),
    q10: str = Form(...),
    q11: str = Form(...),
    q12: str = Form(...),
    q13: str = Form(...),
    q14: str = Form(...),
    token: str = Depends(verify_token)
):
    """
    파일 업로드 & 하이브리드 검증
    
    헤더:
    - Authorization: Bearer YOUR_API_TOKEN
    
    1. 파일 크기/타입 검증
    2. 파일 파싱
    3. AI/ML 정규화 (향후 추가)
    4. Layer 1 검증 (코드 룰)
    5. Layer 2 검증 (ML 이상치)
    6. Layer 3 준비 (챗봇 질문 생성)
    """
    try:
        # 1. 파일 크기 검증 (50MB 제한)
        file_size = len(await file.read())
        await file.seek(0)  # 읽기 포인터 리셋
        
        if file_size > MAX_UPLOAD_SIZE_BYTES:
            logger.warning(f"File too large: {file_size} bytes (max: {MAX_UPLOAD_SIZE_BYTES})")
            raise HTTPException(
                status_code=413,
                detail=f"파일이 너무 큽니다. 최대 50MB까지만 허용됩니다."
            )
        
        # 2. 파일 타입 검증
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="CSV 또는 XLSX 파일만 지원합니다"
            )
        
        # 3. 파일 파싱
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(await file.read()), encoding='utf-8')
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(await file.read()))
        else:
            raise HTTPException(status_code=400, detail="CSV/XLSX 파일만 지원합니다")
        
        # 4. 데이터 크기 검증
        if df.empty:
            logger.warning("Empty file uploaded")
            raise HTTPException(status_code=400, detail="빈 파일입니다")
        
        if len(df) > MAX_ROWS:
            logger.warning(f"Too many rows: {len(df)} (max: {MAX_ROWS})")
            raise HTTPException(
                status_code=413,
                detail=f"행이 너무 많습니다. 최대 50,000행까지만 허용됩니다."
            )
        
        # 5. 세션 생성
        diagnostic_answers = {
            'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5, 
            'q6': q6, 'q7': q7, 'q8': q8, 'q9': q9, 'q10': q10,
            'q11': q11, 'q12': q12, 'q13': q13, 'q14': q14
        }
        session = session_manager.create_session(df, diagnostic_answers)
        logger.info(f"Session created: {session.session_id} (rows: {len(df)}, token: ****)")
        
        # 6. Layer 1 검증 (코드 룰)
        validation_result = validate_layer1(df, diagnostic_answers)
        session.validation_result = validation_result
        
        # 에러를 마스킹해서 반환
        masked_errors = mask_error_list(validation_result.get('errors', []))
        
        # 7. Layer 2 검증 (ML 이상치)
        # column_mapping 자동 추론 (향후: LLM 호출)
        column_mapping = {
            '급여': {'type': 'numeric', 'unit': 'make_won'},
            '생년월일': {'type': 'date', 'format': 'YYYYMMDD'}
        }
        detector = AnomalyDetector()
        anomalies = detector.detect_anomalies(df, column_mapping)
        session.anomalies = anomalies
        
        # 8. Layer 3 준비 (챗봇 질문)
        questions = build_questions(
            validation_result.get('errors', []),
            anomalies,
            column_mapping
        )
        session.chatbot_questions = questions
        
        # 응답 생성 (첫 100행만 반환, 마스킹됨)
        from internal.utils.masking import mask_dataframe
        df_masked = mask_dataframe(df.head(100))
        
        return {
            "session_id": session.session_id,
            "session_token": session.token,
            "row_count": len(df),
            "columns": df.columns.tolist(),
            "data": df_masked.to_dict(orient='records'),
            
            "errors_layer1": masked_errors[:10],  # 첫 10개 (마스킹됨)
            "error_count": len(validation_result.get('errors', [])),
            
            "anomalies_layer2": anomalies[:10],  # 첫 10개
            "anomaly_count": len(anomalies),
            
            "chatbot_questions": questions,
            "message": "파일 업로드 성공. 질문에 답변해주세요."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """세션 데이터 조회"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return {
        "session_id": session.session_id,
        "row_count": len(session.current_dataframe),
        "modified_count": session.get_modified_count(),
        "data": session.current_dataframe.to_dict(orient='records'),
        "errors": session.validation_result.get('errors', []),
        "anomalies": session.anomalies,
        "questions": session.chatbot_questions,
        "answers": session.chatbot_answers
    }


@app.post("/chat/{session_id}")
def chat(session_id: str, question_id: str, answer: str, action: str = "auto_fix"):
    """
    챗봇 질문에 답변
    
    action: "auto_fix" | "manual_edit" | "skip"
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    try:
        # 답변 저장
        session.chatbot_answers[question_id] = answer
        
        # 답변 기반 자동 수정 (향후: LLM 호출)
        if action == "auto_fix":
            # 예시: "q1" → 해당 행 수정
            pass
        
        # 다음 질문 찾기
        next_question = None
        for q in session.chatbot_questions:
            if q['id'] not in session.chatbot_answers:
                next_question = q
                break
        
        return {
            "success": True,
            "message": f"답변이 저장되었습니다",
            "next_question": next_question,
            "progress": f"{len(session.chatbot_answers)}/{len(session.chatbot_questions)}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-cell/{session_id}")
def update_cell(session_id: str, row: int, column: str, new_value: str):
    """수동 셀 편집"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    try:
        # 원본 값 저장
        original_value = session.current_dataframe.iloc[row][column]
        
        # 셀 수정
        session.current_dataframe.iloc[row, session.current_dataframe.columns.get_loc(column)] = new_value
        
        # 수정 이력 저장
        key = f"{row}_{column}"
        session.modified_cells[key] = {
            "original": str(original_value),
            "new": str(new_value),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": f"행 {row}, 열 '{column}' 수정 완료",
            "modified_count": session.get_modified_count()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{session_id}")
def download(session_id: str):
    """CSV 다운로드"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    try:
        # CSV 생성
        csv_buffer = io.BytesIO()
        session.current_dataframe.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        
        # 임시 파일 저장
        temp_path = f"/tmp/wikisoft2_{session.session_id}.csv"
        session.current_dataframe.to_csv(temp_path, index=False, encoding='utf-8-sig')
        
        # 세션 삭제
        session_manager.delete_session(session_id)
        
        return FileResponse(
            path=temp_path,
            filename=f"validated_{session.session_id[:8]}.csv",
            media_type="text/csv"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
def cleanup_expired_sessions():
    """만료된 세션 정리 (관리자용)"""
    session_manager.cleanup_expired()
    return {"message": "만료된 세션 정리 완료"}


@app.get("/diagnostic-questions")
def get_diagnostic_questions():
    """
    확장된 진단 질문 목록 반환 (28개)
    - 14개 데이터 품질 질문
    - 3개 재무적 가정 질문
    - 3개 퇴직금 설정 질문
    - 8개 집계값 질문 (Layer 2 검증 대상)
    """
    from internal.ai.diagnostic_questions import format_question_for_chatbot, QUESTION_SUMMARY
    
    questions_formatted = []
    for q in ALL_QUESTIONS:
        questions_formatted.append({
            "id": q["id"],
            "type": q["type"],
            "category": q["category"],
            "question": format_question_for_chatbot(q),
            "choices": q.get("choices"),
            "unit": q.get("unit"),
            "requires_validation": q.get("validate_against") is not None
        })
    
    return {
        "questions": questions_formatted,
        "summary": QUESTION_SUMMARY
    }


@app.post("/validate-with-roster")
async def validate_with_roster(
    file: UploadFile = File(...),
    chatbot_answers: str = Form(...),
    token: str = Depends(verify_token)
):
    """
    명부 파일 + 챗봇 답변 → Layer 2 검증
    
    헤더:
        Authorization: Bearer YOUR_API_TOKEN (프로덕션)
    
    Request:
        - file: 명부 파일 (xls/xlsx)
        - chatbot_answers: JSON 문자열 {"q21": 17, "q22": 664, ...}
    
    Response:
        {
            "validation": {
                "status": "passed" | "warnings" | "failed",
                "total_checks": 8,
                "passed": 6,
                "warnings": [...]
            },
            "calculated_aggregates": {...},
            "parsing_warnings": [...],
            "session_id": "..."
        }
    """
    import sys
    from io import StringIO
    
    try:
        request_id = str(uuid4())[:8]
        
        # 1. 파일 검증
        structured_logger.info("validate_with_roster_start", request_id=request_id)
        
        content = await validate_file(file)
        
        # 2. 챗봇 답변 파싱
        try:
            answers = json.loads(chatbot_answers)
        except json.JSONDecodeError:
            structured_logger.warning("chatbot_answers_json_invalid", request_id=request_id)
            raise HTTPException(
                status_code=400,
                detail="❌ 챗봇 답변이 유효한 JSON 형식이 아닙니다"
            )
        
        # Pydantic 검증
        try:
            ChatbotAnswersModel(answers=answers)
        except Exception as e:
            structured_logger.warning(
                "chatbot_answers_validation_error",
                request_id=request_id,
                error=str(e)
            )
            raise HTTPException(status_code=422, detail=f"❌ {str(e)}")
        
        # 3. 명부 파싱 시 경고 캡처
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            calculated = aggregate_from_excel(content)
        finally:
            sys.stdout = old_stdout
        
        # 파싱 경고 추출
        parsing_warnings = []
        for line in captured_output.getvalue().split('\n'):
            line = line.strip()
            if line.startswith('❌'):
                parsing_warnings.append({
                    "severity": "error",
                    "message": line.replace('❌', '').strip()
                })
            elif line.startswith('⚠️'):
                parsing_warnings.append({
                    "severity": "warning",
                    "message": line.replace('⚠️', '').strip()
                })
        
        # 4. Layer 2 검증 실행
        validation_result = validate_chatbot_answers(answers, calculated, tolerance_percent=5.0)
        
        # 5. 임시 세션 생성
        df_placeholder = pd.DataFrame()
        session = session_manager.create_session(df_placeholder, answers)
        session.calculated_aggregates = calculated
        session.validation_result = validation_result
        
        structured_logger.info(
            "validate_with_roster_success",
            request_id=request_id,
            session_id=session.session_id,
            checks=validation_result['total_checks'],
            passed=validation_result['passed']
        )
        
        return {
            "validation": validation_result,
            "calculated_aggregates": {
                "counts_I26_I39": calculated["counts_I26_I39"],
                "sums_I40_I51": calculated["sums_I40_I51"]
            },
            "parsing_warnings": parsing_warnings,
            "session_id": session.session_id,
            "message": "✅ 검증 완료"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error("validate_with_roster_error", exc=e)
        raise HTTPException(status_code=500, detail="❌ 검증 중 오류가 발생했습니다")


@app.post("/generate-with-validation")
async def generate_with_validation(
    session_id: str = Form(...),
    company_name: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    작성기준일: str = Form(None),
    token: str = Depends(verify_token)
):
    """
    검증 완료된 세션으로 (1-2) Excel 파일 생성 및 다운로드
    
    헤더:
        Authorization: Bearer YOUR_API_TOKEN (프로덕션)
    
    Request:
        - session_id: /validate-with-roster에서 받은 세션 ID
        - company_name, phone, email: 회사 정보 (선택)
        - 작성기준일: YYYYMMDD (선택, 기본값 오늘)
    
    Response:
        Excel 파일 다운로드 (검증 경고가 있으면 빨간 배경 + 코멘트 표시)
    """
    try:
        request_id = str(uuid4())[:8]
        structured_logger.info("generate_with_validation_start", request_id=request_id, session_id=session_id)
        
        # 세션 조회
        session = session_manager.get_session(session_id)
        if not session:
            structured_logger.warning("session_not_found", request_id=request_id, session_id=session_id)
            raise HTTPException(
                status_code=404,
                detail="❌ 세션을 찾을 수 없습니다. 다시 검증을 실행해주세요."
            )
        
        # 세션에서 챗봇 답변 및 검증 결과 가져오기
        chatbot_answers = session.diagnostic_answers
        validation_result = getattr(session, 'validation_result', None)
        
        if validation_result is None:
            structured_logger.warning("validation_result_missing", request_id=request_id, session_id=session_id)
            raise HTTPException(
                status_code=400,
                detail="❌ 검증 결과가 없습니다. /validate-with-roster를 먼저 호출하세요."
            )
        
        # 회사 정보
        company_info = {}
        if company_name:
            company_info['회사명'] = company_name
        if phone:
            company_info['전화번호'] = phone
        if email:
            company_info['이메일'] = email
        
        # 작성기준일 기본값
        if not 작성기준일:
            작성기준일 = datetime.now().strftime('%Y%m%d')
        
        # Excel 생성 (검증 경고 포함)
        warnings = validation_result.get('warnings', [])
        excel_bytes = save_sheet_1_2_from_chatbot_to_bytes(
            chatbot_answers,
            validation_warnings=warnings,
            company_info=company_info,
            작성기준일=작성기준일
        )
        
        # 파일명
        filename = f"퇴직급여채무_{company_name or 'unknown'}_{작성기준일}.xlsx"
        
        # 세션 정리
        session_manager.delete_session(session_id)
        
        structured_logger.info(
            "generate_with_validation_success",
            request_id=request_id,
            session_id=session_id,
            filename=filename,
            file_size=len(excel_bytes)
        )
        
        return FileResponse(
            path=io.BytesIO(excel_bytes),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error("generate_with_validation_error", request_id=request_id, exc=e)
        raise HTTPException(status_code=500, detail="❌ Excel 파일 생성 중 오류가 발생했습니다")


# ============================================
# v2.2: Batch Validate API (여러 파일 한번에 검증)
# ============================================

class BatchValidateItem(BaseModel):
    """배치 검증 항목"""
    file_name: str
    overall_confidence: float
    decision: Dict[str, Any]
    status: str  # "passed", "needs_review", "failed"


class BatchValidateResponse(BaseModel):
    """배치 검증 응답"""
    success: bool
    total_files: int
    processed_files: int
    results: List[BatchValidateItem]
    summary: Dict[str, Any]
    execution_time: float


@app.post("/batch-validate", response_model=BatchValidateResponse)
async def batch_validate(
    files: List[UploadFile] = File(...),
    token: str = Depends(verify_token),
    request: Request = None
) -> BatchValidateResponse:
    """
    배치 검증 엔드포인트 (여러 파일 한번에 검증)
    
    최대 10개 파일까지 동시 검증 가능
    
    curl -X POST \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -F "files=@file1.xlsx" \
      -F "files=@file2.xlsx" \
      http://localhost:8000/batch-validate
    """
    request_id = request.headers.get("x-request-id", str(uuid4())[:8]) if request else str(uuid4())[:8]
    
    try:
        import time
        start_time = time.time()
        
        # 파일 수 제한
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="❌ 최대 10개 파일까지만 가능합니다"
            )
        
        structured_logger.info(
            "batch_validate_start",
            request_id=request_id,
            file_count=len(files)
        )
        
        results: List[BatchValidateItem] = []
        auto_complete_count = 0
        ask_human_count = 0
        reject_count = 0
        
        # 파일 병렬 검증 (실제로는 순차 처리, 비동기 최적화는 나중에)
        for file in files:
            try:
                # 파일 검증
                content = await validate_file(file)
                
                # Excel 파싱
                df = pd.read_excel(io.BytesIO(content), sheet_name=0)
                
                # ReACT Loop 실행
                react_result = await react_loop.run(
                    file_path=file.filename,
                    task="validate",
                    max_steps=3,
                    confidence_threshold=0.85
                )
                
                if not react_result.get("success"):
                    results.append(BatchValidateItem(
                        file_name=file.filename,
                        overall_confidence=0.0,
                        decision={
                            "type": "error",
                            "message": react_result.get("error", "Unknown error")
                        },
                        status="failed"
                    ))
                    continue
                
                # Confidence 계산
                overall_confidence = react_result.get("result", {}).get("confidence", 0.5)
                
                # Decision Engine
                decision = await decision_engine.decide(
                    confidence=overall_confidence,
                    data={"file": file.filename, "rows": len(df)},
                    result={"success": True},
                    context={"batch": True}
                )
                
                # 상태 결정
                if decision.type.value == "auto_complete":
                    status = "passed"
                    auto_complete_count += 1
                elif decision.type.value == "ask_human":
                    status = "needs_review"
                    ask_human_count += 1
                else:
                    status = "failed"
                    reject_count += 1
                
                results.append(BatchValidateItem(
                    file_name=file.filename,
                    overall_confidence=round(overall_confidence, 3),
                    decision={
                        "type": decision.type.value,
                        "reason": decision.reason.value,
                        "message": decision.message,
                    },
                    status=status
                ))
                
            except HTTPException:
                raise
            except Exception as e:
                results.append(BatchValidateItem(
                    file_name=file.filename,
                    overall_confidence=0.0,
                    decision={
                        "type": "error",
                        "message": str(e)
                    },
                    status="failed"
                ))
        
        execution_time = time.time() - start_time
        
        response = BatchValidateResponse(
            success=True,
            total_files=len(files),
            processed_files=len(results),
            results=results,
            summary={
                "passed": auto_complete_count,
                "needs_review": ask_human_count,
                "failed": reject_count,
                "pass_rate": round(auto_complete_count / len(results), 3) if results else 0,
                "avg_confidence": round(
                    sum(r.overall_confidence for r in results) / len(results), 3
                ) if results else 0,
            },
            execution_time=round(execution_time, 3)
        )
        
        structured_logger.info(
            "batch_validate_success",
            request_id=request_id,
            total_files=len(files),
            passed=auto_complete_count,
            needs_review=ask_human_count,
            failed=reject_count,
            execution_time=execution_time
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error(
            "batch_validate_error",
            request_id=request_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"❌ 배치 검증 중 오류: {str(e)}"
        )


if __name__ == "__main__":
    if USE_HTTPS:
        uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=SSL_KEYFILE, ssl_certfile=SSL_CERTFILE)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)

