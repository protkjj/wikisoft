"""
Authentication Routes

JWT 기반 인증 API 엔드포인트
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from core.security.auth import (
    create_access_token,
    verify_token,
    User,
    TokenData,
)
from core.security.config import security_settings
from core.security.audit import log_action, AuditAction

router = APIRouter()
security = HTTPBearer(auto_error=False)


# ========================================
# In-Memory User Store (데모용 - 추후 DB 연동)
# ========================================

# Note: 비밀번호는 평문 저장 (데모용)
# 프로덕션에서는 반드시 해싱하여 저장해야 함
_users_db: dict[str, dict] = {
    "admin": {
        "id": "admin",
        "email": "admin@onecheck.com",
        "name": "관리자",
        "role": "admin",
        "password": "admin1234!",  # 데모용 평문
        "is_active": True,
        "scopes": ["admin", "read", "write", "delete"],
    },
    "user": {
        "id": "user",
        "email": "user@onecheck.com",
        "name": "사용자",
        "role": "user",
        "password": "user1234!",  # 데모용 평문
        "is_active": True,
        "scopes": ["read", "write"],
    },
}


# ========================================
# Request/Response Models
# ========================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)


class RegisterRequest(BaseModel):
    """회원가입 요청"""
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)  # 간단한 이메일 검증
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: str
    email: str
    name: str
    role: str
    scopes: list[str]


# ========================================
# Helper Functions
# ========================================

def get_user_by_username(username: str) -> Optional[dict]:
    """사용자명으로 사용자 조회"""
    return _users_db.get(username)


def get_user_by_email(email: str) -> Optional[dict]:
    """이메일로 사용자 조회"""
    for user in _users_db.values():
        if user["email"] == email:
            return user
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: Optional[str] = Header(None),
) -> Optional[User]:
    """현재 인증된 사용자 가져오기"""
    token = None

    # Bearer token from HTTPBearer
    if credentials:
        token = credentials.credentials
    # Or from Authorization header directly
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        return None

    token_data = verify_token(token)
    if not token_data:
        return None

    user_data = get_user_by_username(token_data.sub)
    if not user_data:
        return None

    return User(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"],
        is_active=user_data["is_active"],
        scopes=user_data["scopes"],
    )


def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """인증 필수 의존성"""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(require_auth)) -> User:
    """관리자 권한 필수 의존성"""
    if user.role != "admin" and "admin" not in user.scopes:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다",
        )
    return user


# ========================================
# Auth Endpoints
# ========================================

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    로그인 및 JWT 토큰 발급

    데모 계정:
    - admin / admin1234! (관리자)
    - user / user1234! (일반 사용자)
    """
    user = get_user_by_username(request.username)

    if not user:
        log_action(
            AuditAction.AUTH_LOGIN_FAILED,
            details={"username": request.username, "reason": "user_not_found"},
            success=False,
        )
        raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호")

    # 데모용: 평문 비교 (프로덕션에서는 hash 비교)
    if request.password != user["password"]:
        log_action(
            AuditAction.AUTH_LOGIN_FAILED,
            user_id=user["id"],
            details={"reason": "invalid_password"},
            success=False,
        )
        raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

    # Create access token
    expires_delta = timedelta(minutes=security_settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        user_id=user["id"],
        scopes=user["scopes"],
        expires_delta=expires_delta,
    )

    log_action(
        AuditAction.AUTH_LOGIN,
        user_id=user["id"],
        user_email=user["email"],
        user_role=user["role"],
        details={"scopes": user["scopes"]},
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=security_settings.jwt_access_token_expire_minutes * 60,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "scopes": user["scopes"],
        },
    )


@router.post("/auth/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    회원가입 (데모용 - 메모리에 저장)
    """
    # Check if username exists
    if get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

    # Check if email exists
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    # Validate password strength
    if len(request.password) < security_settings.password_min_length:
        raise HTTPException(
            status_code=400,
            detail=f"비밀번호는 최소 {security_settings.password_min_length}자 이상이어야 합니다"
        )

    # Create user
    new_user = {
        "id": request.username,
        "email": request.email,
        "name": request.name,
        "role": "user",
        "password": request.password,  # 데모용 평문
        "is_active": True,
        "scopes": ["read", "write"],
    }

    _users_db[request.username] = new_user

    log_action(
        AuditAction.USER_CREATE,
        user_id=new_user["id"],
        user_email=new_user["email"],
        details={"role": new_user["role"]},
    )

    return UserResponse(
        id=new_user["id"],
        email=new_user["email"],
        name=new_user["name"],
        role=new_user["role"],
        scopes=new_user["scopes"],
    )


@router.post("/auth/logout")
async def logout(user: User = Depends(require_auth)):
    """
    로그아웃 (토큰 무효화)

    Note: Stateless JWT는 서버에서 무효화 불가.
    클라이언트에서 토큰 삭제 필요.
    프로덕션에서는 토큰 블랙리스트 사용 권장.
    """
    log_action(
        AuditAction.AUTH_LOGOUT,
        user_id=user.id,
        user_email=user.email,
    )

    return {"message": "로그아웃 되었습니다", "user_id": user.id}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    """현재 로그인된 사용자 정보"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        scopes=user.scopes,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(user: User = Depends(require_auth)):
    """
    토큰 갱신

    현재 유효한 토큰으로 새 토큰 발급
    """
    expires_delta = timedelta(minutes=security_settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        user_id=user.id,
        scopes=user.scopes,
        expires_delta=expires_delta,
    )

    log_action(
        AuditAction.AUTH_TOKEN_REFRESH,
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=security_settings.jwt_access_token_expire_minutes * 60,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "scopes": user.scopes,
        },
    )


@router.get("/auth/verify")
async def verify_auth(user: Optional[User] = Depends(get_current_user)):
    """
    토큰 유효성 검증

    인증 헤더 없이도 호출 가능 (상태 확인용)
    """
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
            }
        }
    return {"authenticated": False}


# ========================================
# Admin Endpoints
# ========================================

@router.get("/auth/users", response_model=list[UserResponse])
async def list_users(admin: User = Depends(require_admin)):
    """
    모든 사용자 목록 (관리자 전용)
    """
    return [
        UserResponse(
            id=u["id"],
            email=u["email"],
            name=u["name"],
            role=u["role"],
            scopes=u["scopes"],
        )
        for u in _users_db.values()
    ]
