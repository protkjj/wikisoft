from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict
import pandas as pd
import uuid
import os
import io
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

app = FastAPI(title="WIKISOFT HR Validation API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경 변수
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REQUIRE_SESSION_TOKEN = os.getenv("REQUIRE_SESSION_TOKEN", "false").lower() == "true"
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "50"))

# AI 클라이언트 초기화
try:
    from internal.ai import AIProcessor
    ai_processor = AIProcessor(api_key=OPENAI_API_KEY)
except Exception:
    ai_processor = None

@dataclass
class Session:
    """세션 데이터 클래스"""
    session_id: str
    original_dataframe: pd.DataFrame
    current_dataframe: pd.DataFrame
    validation_result: dict
    created_at: datetime
    last_accessed: datetime
    token: str = ""
    modified_cells: Dict = field(default_factory=dict)

class SessionManager:
    """세션 관리자"""
    def __init__(self, ttl_minutes: int = 60, max_sessions: int = 50):
        self.sessions: Dict[str, Session] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_sessions = max_sessions
    
    def create_session(self, df: pd.DataFrame, validation_result: dict) -> tuple[str, str]:
        """새 세션 생성"""
        self._cleanup_expired()
        
        # 용량 초과 시 가장 오래된 세션 삭제 (LRU)
        if len(self.sessions) >= self.max_sessions:
            oldest_id = min(self.sessions.keys(), 
                          key=lambda k: self.sessions[k].last_accessed)
            del self.sessions[oldest_id]
        
        session_id = str(uuid.uuid4())
        token = str(uuid.uuid4()).replace('-', '')
        
        session = Session(
            session_id=session_id,
            original_dataframe=df.copy(),
            current_dataframe=df.copy(),
            validation_result=validation_result,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            token=token
        )
        self.sessions[session_id] = session
        return session_id, token
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """세션 조회"""
        self._cleanup_expired()
        session = self.sessions.get(session_id)
        if session:
            session.last_accessed = datetime.now()
        return session
    
    def _cleanup_expired(self):
        """만료된 세션 정리"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_accessed > self.ttl
        ]
        for sid in expired:
            del self.sessions[sid]

session_manager = SessionManager(ttl_minutes=60, max_sessions=MAX_SESSIONS)

def _require_token(request: Request, session: Session):
    """토큰 검증 (옵션)"""
    if not REQUIRE_SESSION_TOKEN:
        return
    
    # Authorization 헤더 또는 쿼리 파라미터
    auth_header = request.headers.get("Authorization", "")
    token_from_header = auth_header.replace("Bearer ", "") if auth_header else None
    token_from_query = request.query_params.get("token")
    
    provided_token = token_from_header or token_from_query
    
    if not provided_token or provided_token != session.token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

@app.get("/")
async def root():
    return {"message": "WIKISOFT HR Validation API", "status": "running"}

@app.post("/validate")
async def validate(file: UploadFile):
    """
    파일 업로드 & 검증
    
    TODO: AI 통합 후 수정 필요
    """
    try:
        # 파일 로드
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # AI 정규화 + 검증 (internal/ai/client.py)
        column_mapping = {col: "업로드된 컬럼" for col in df.columns}
        if ai_processor:
            validation_result = ai_processor.normalize_and_validate(df, column_mapping)
        else:
            validation_result = {"errors": [], "summary": "AI 비활성화"}
        
        # 세션 생성
        session_id, token = session_manager.create_session(df, validation_result)
        
        return {
            "session_id": session_id,
            "session_token": token,
            "validation": validation_result,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session_data(session_id: str, request: Request):
    """세션 데이터 조회"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _require_token(request, session)
    
    df = session.current_dataframe
    
    return {
        "session_id": session_id,
        "data": df.to_dict(orient='records'),
        "columns": df.columns.tolist(),
        "validation": session.validation_result,
        "modified_cells": session.modified_cells
    }

@app.post("/update-cell")
async def update_cell(
    session_id: str,
    row: int,
    column: str,
    value: str,
    request: Request
):
    """셀 업데이트"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _require_token(request, session)
    
    try:
        # 셀 업데이트
        session.current_dataframe.at[row, column] = value
        
        # 수정 이력 기록
        cell_key = f"{row}_{column}"
        session.modified_cells[cell_key] = value
        
        # TODO: 재검증 (AI)
        
        return {
            "success": True,
            "message": "Cell updated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-fix/{session_id}")
async def auto_fix(session_id: str, request: Request):
    """AI 자동수정"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _require_token(request, session)
    
    df = session.current_dataframe
    column_mapping = {col: "업로드된 컬럼" for col in df.columns}
    corrections_applied = 0

    # AI 결과가 있다면 normalized_data 적용
    ai_result = None
    if ai_processor:
        ai_result = ai_processor.normalize_and_validate(df, column_mapping)

    normalized_rows = []
    if ai_result and isinstance(ai_result, dict):
        normalized_rows = ai_result.get("normalized_data") or []

    try:
        for item in normalized_rows:
            row = item.get("row")
            columns = item.get("columns", {})
            if row is None:
                continue
            # 1-based → 0-based 변환 시도
            idx = int(row) - 1 if isinstance(row, int) else row
            for col, val in columns.items():
                if col in df.columns and 0 <= idx < len(df):
                    df.at[idx, col] = val
                    corrections_applied += 1
        session.current_dataframe = df
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    remaining_errors = len(ai_result.get("errors", [])) if ai_result else 0
    return {
        "message": "자동 수정 완료",
        "remaining_errors": remaining_errors,
        "corrections_applied": corrections_applied
    }

@app.get("/download/{session_id}")
async def download(session_id: str, request: Request):
    """CSV 다운로드 (UTF-8 BOM + RFC5987)"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _require_token(request, session)
    
    # CSV 생성
    csv_buffer = io.StringIO()
    session.current_dataframe.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_text = csv_buffer.getvalue()
    
    # UTF-8 BOM 추가
    csv_bytes = csv_text.encode('utf-8-sig')
    
    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wikisoft_수정본_{timestamp}.csv"
    
    # RFC5987 헤더
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{quote(filename)}',
        'Content-Type': 'text/csv; charset=utf-8'
    }
    
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type='text/csv',
        headers=headers
    )

@app.post("/chat")
async def chat(
    session_id: str,
    message: str,
    request: Request
):
    """AI 챗봇"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    _require_token(request, session)
    
    df = session.current_dataframe
    column_mapping = {col: "업로드된 컬럼" for col in df.columns}

    if ai_processor:
        result = ai_processor.chat(df, message, column_mapping)
        return result
    else:
        return {
            "response": "AI가 비활성화되어 있습니다.",
            "function_call": None
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
