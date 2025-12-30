from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import batch, diagnostic_questions, health, validate

app = FastAPI(title="WIKISOFT3 API", version="0.0.1")

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3004", "http://127.0.0.1:3003", "http://127.0.0.1:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (/api prefix)
app.include_router(health.router, prefix="/api")
app.include_router(diagnostic_questions.router, prefix="/api")
app.include_router(validate.router, prefix="/api")
app.include_router(batch.router, prefix="/api")

# 기존 경로도 유지 (하위 호환)
app.include_router(health.router)
app.include_router(diagnostic_questions.router)
app.include_router(validate.router)
app.include_router(batch.router)
