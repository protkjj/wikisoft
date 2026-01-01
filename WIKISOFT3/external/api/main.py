import os
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import agent, batch, diagnostic_questions, health, validate, react_agent, learn, windmill, tools, export

app = FastAPI(title="WIKISOFT3 API", version="0.0.1")


# ============================================================
# Rate Limiting (간단한 인메모리 방식)
# ============================================================
class RateLimiter:
    """IP 기반 Rate Limiting."""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        요청 허용 여부 확인.
        
        Returns:
            (허용 여부, 남은 요청 수)
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # 1분 이내 요청만 유지
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        
        if remaining <= 0:
            return False, 0
        
        self.requests[client_ip].append(now)
        return True, remaining - 1


rate_limiter = RateLimiter(requests_per_minute=60)  # 분당 60개 요청


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate Limiting 미들웨어."""
    # 헬스체크는 제외
    if request.url.path in ["/api/health", "/health"]:
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    is_allowed, remaining = rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."}
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# ============================================================
# CORS 설정 (강화)
# ============================================================
# 환경에 따라 설정
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
    "http://localhost:3006",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:3004",
    "http://127.0.0.1:3005",
    "http://127.0.0.1:3006",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # 학습 API용 DELETE 추가
    allow_headers=["Content-Type", "Authorization"],  # 필요한 헤더만 허용
    max_age=3600,  # preflight 캐시 1시간
)

# 라우터 등록 (/api prefix)
app.include_router(health.router, prefix="/api")
app.include_router(diagnostic_questions.router, prefix="/api")
app.include_router(validate.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(react_agent.router, prefix="/api")
app.include_router(learn.router, prefix="/api")
app.include_router(windmill.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(export.router, prefix="/api")

# 기존 경로도 유지 (하위 호환)
app.include_router(health.router)
app.include_router(diagnostic_questions.router)
app.include_router(validate.router)
app.include_router(batch.router)
app.include_router(agent.router)
app.include_router(react_agent.router)
app.include_router(learn.router)
app.include_router(windmill.router)
app.include_router(tools.router)
app.include_router(export.router)

# 테스트 파일 서빙 (Windmill 테스트용)
TEST_FILES_DIR = Path(__file__).parent.parent.parent / "test_files"
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

@app.get("/files/{filename}")
async def serve_test_file(filename: str):
    """테스트 파일 다운로드 엔드포인트"""
    # Path Traversal 방지: 파일명에서 경로 구분자 제거
    safe_filename = os.path.basename(filename)

    # 허용된 확장자만 허용
    ext = Path(safe_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="허용되지 않은 파일 형식입니다")

    # 경로 검증
    file_path = (TEST_FILES_DIR / safe_filename).resolve()
    if not str(file_path).startswith(str(TEST_FILES_DIR.resolve())):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(file_path, filename=safe_filename)
