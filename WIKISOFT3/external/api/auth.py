"""
API 인증 미들웨어
Bearer Token 방식 사용
"""
import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Bearer Token 검증

    환경변수 API_TOKEN과 비교
    """
    expected_token = os.getenv("API_TOKEN")

    if not expected_token:
        # 개발 편의: 환경변수 없으면 경고만 하고 통과
        print("⚠️ WARNING: API_TOKEN not set - authentication disabled!")
        return "dev-mode"

    provided_token = credentials.credentials

    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return provided_token
