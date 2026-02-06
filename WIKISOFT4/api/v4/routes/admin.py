"""
Admin Routes

관리자 전용 API 엔드포인트
- 사용자 관리
- 감사 로그 조회
- 학습 데이터 관리
- 시스템 설정
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from core.security.auth import User
from core.security.audit import (
    log_action,
    AuditAction,
    get_audit_trail,
    AuditEntry,
)
from core.admin.settings_store import (
    get_settings,
    update_settings,
    SystemSettings,
)
from core.admin.training_manager import (
    get_training_manager,
    TrainingFile,
    TrainingFileDetail,
)
from .auth import require_admin, _users_db, get_user_by_username, get_user_by_email

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================

class UserCreateRequest(BaseModel):
    """사용자 생성 요청."""
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user", pattern="^(user|admin)$")


class UserUpdateRequest(BaseModel):
    """사용자 수정 요청."""
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    """사용자 응답."""
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    scopes: list[str]


class AuditLogResponse(BaseModel):
    """감사 로그 응답."""
    entries: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class SettingsUpdateRequest(BaseModel):
    """설정 업데이트 요청."""
    minimum_wage: Optional[int] = Field(None, ge=0)
    retirement_age: Optional[int] = Field(None, ge=0, le=100)
    validation_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_file_size_mb: Optional[int] = Field(None, ge=1, le=500)
    allowed_extensions: Optional[list[str]] = None


# ========================================
# User Management
# ========================================

@router.get("/admin/users", response_model=list[UserResponse])
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
            is_active=u["is_active"],
            scopes=u["scopes"],
        )
        for u in _users_db.values()
    ]


@router.post("/admin/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    admin: User = Depends(require_admin)
):
    """
    사용자 생성 (관리자 전용)
    """
    # Check if username exists
    if get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

    # Check if email exists
    if get_user_by_email(request.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    # Determine scopes based on role
    scopes = ["admin", "read", "write", "delete"] if request.role == "admin" else ["read", "write"]

    # Create user
    new_user = {
        "id": request.username,
        "email": request.email,
        "name": request.name,
        "role": request.role,
        "password": request.password,  # 데모용 평문
        "is_active": True,
        "scopes": scopes,
    }

    _users_db[request.username] = new_user

    log_action(
        AuditAction.USER_CREATE,
        user_id=admin.id,
        user_email=admin.email,
        user_role=admin.role,
        resource_type="user",
        resource_id=new_user["id"],
        details={"created_user": request.username, "role": request.role},
    )

    return UserResponse(
        id=new_user["id"],
        email=new_user["email"],
        name=new_user["name"],
        role=new_user["role"],
        is_active=new_user["is_active"],
        scopes=new_user["scopes"],
    )


@router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    admin: User = Depends(require_admin)
):
    """
    사용자 수정 (관리자 전용)
    """
    user = _users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # Prevent self-demotion
    if user_id == admin.id and request.role and request.role != "admin":
        raise HTTPException(status_code=400, detail="자신의 역할은 변경할 수 없습니다")

    # Prevent self-deactivation
    if user_id == admin.id and request.is_active is False:
        raise HTTPException(status_code=400, detail="자신을 비활성화할 수 없습니다")

    # Check email uniqueness if changing
    if request.email and request.email != user["email"]:
        existing = get_user_by_email(request.email)
        if existing and existing["id"] != user_id:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    # Track changes for audit
    changes = {}

    # Update fields
    if request.email is not None:
        changes["email"] = {"from": user["email"], "to": request.email}
        user["email"] = request.email

    if request.name is not None:
        changes["name"] = {"from": user["name"], "to": request.name}
        user["name"] = request.name

    if request.role is not None:
        changes["role"] = {"from": user["role"], "to": request.role}
        user["role"] = request.role
        # Update scopes based on role
        user["scopes"] = ["admin", "read", "write", "delete"] if request.role == "admin" else ["read", "write"]

    if request.is_active is not None:
        changes["is_active"] = {"from": user["is_active"], "to": request.is_active}
        user["is_active"] = request.is_active

    if request.password is not None:
        changes["password"] = "changed"
        user["password"] = request.password

    log_action(
        AuditAction.USER_UPDATE,
        user_id=admin.id,
        user_email=admin.email,
        user_role=admin.role,
        resource_type="user",
        resource_id=user_id,
        details={"changes": changes},
    )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        is_active=user["is_active"],
        scopes=user["scopes"],
    )


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin)
):
    """
    사용자 삭제 (관리자 전용)
    """
    if user_id not in _users_db:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # Prevent self-deletion
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="자신을 삭제할 수 없습니다")

    deleted_user = _users_db.pop(user_id)

    log_action(
        AuditAction.USER_DELETE,
        user_id=admin.id,
        user_email=admin.email,
        user_role=admin.role,
        resource_type="user",
        resource_id=user_id,
        details={"deleted_user": user_id, "email": deleted_user["email"]},
    )

    return {"message": f"사용자 '{user_id}'가 삭제되었습니다"}


# ========================================
# Audit Log
# ========================================

@router.get("/admin/audit", response_model=AuditLogResponse)
async def get_audit_logs(
    admin: User = Depends(require_admin),
    action: Optional[str] = Query(None, description="액션 필터 (예: auth.login)"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    start_date: Optional[str] = Query(None, description="시작일 (ISO 형식)"),
    end_date: Optional[str] = Query(None, description="종료일 (ISO 형식)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """
    감사 로그 조회 (관리자 전용)
    """
    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 시작일 형식")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 종료일 형식")

    # Parse action enum
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            # Allow filtering by partial match
            pass

    entries = get_audit_trail(
        user_id=user_id,
        action=action_enum,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset,
    )

    return AuditLogResponse(
        entries=[e.model_dump() for e in entries],
        total=len(entries),
        limit=limit,
        offset=offset,
    )


# ========================================
# Training Data Management
# ========================================

@router.get("/admin/training-data")
async def list_training_data(
    admin: User = Depends(require_admin),
    file_type: Optional[str] = Query(None, description="파일 타입 필터"),
):
    """
    학습 데이터 파일 목록 (관리자 전용)
    """
    manager = get_training_manager()
    files = manager.list_files()

    if file_type:
        files = [f for f in files if f.file_type == file_type]

    stats = manager.get_stats()

    return {
        "files": [f.model_dump() for f in files],
        "stats": stats,
    }


@router.get("/admin/training-data/{filename}")
async def get_training_data(
    filename: str,
    admin: User = Depends(require_admin),
):
    """
    학습 데이터 파일 상세 조회 (관리자 전용)
    """
    manager = get_training_manager()
    file_detail = manager.get_file(filename)

    if file_detail is None:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    return file_detail.model_dump()


@router.delete("/admin/training-data/{filename}")
async def delete_training_data(
    filename: str,
    admin: User = Depends(require_admin),
):
    """
    학습 데이터 파일 삭제 (관리자 전용)
    """
    manager = get_training_manager()

    if not manager.delete_file(filename):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없거나 삭제할 수 없습니다")

    log_action(
        AuditAction.DATA_DELETE,
        user_id=admin.id,
        user_email=admin.email,
        user_role=admin.role,
        resource_type="training_data",
        resource_id=filename,
        details={"deleted_file": filename},
    )

    return {"message": f"파일 '{filename}'이 삭제되었습니다"}


# ========================================
# System Settings
# ========================================

@router.get("/admin/settings")
async def get_system_settings(
    admin: User = Depends(require_admin),
):
    """
    시스템 설정 조회 (관리자 전용)
    """
    settings = get_settings()
    return settings.model_dump()


@router.put("/admin/settings")
async def update_system_settings(
    request: SettingsUpdateRequest,
    admin: User = Depends(require_admin),
):
    """
    시스템 설정 수정 (관리자 전용)
    """
    # Build update dict with only provided fields
    updates = {}
    if request.minimum_wage is not None:
        updates["minimum_wage"] = request.minimum_wage
    if request.retirement_age is not None:
        updates["retirement_age"] = request.retirement_age
    if request.validation_confidence_threshold is not None:
        updates["validation_confidence_threshold"] = request.validation_confidence_threshold
    if request.max_file_size_mb is not None:
        updates["max_file_size_mb"] = request.max_file_size_mb
    if request.allowed_extensions is not None:
        updates["allowed_extensions"] = request.allowed_extensions

    if not updates:
        raise HTTPException(status_code=400, detail="수정할 항목이 없습니다")

    old_settings = get_settings().model_dump()
    new_settings = update_settings(updates)

    log_action(
        AuditAction.DATA_UPDATE,
        user_id=admin.id,
        user_email=admin.email,
        user_role=admin.role,
        resource_type="system_settings",
        details={"old": old_settings, "new": new_settings.model_dump(), "changes": updates},
    )

    return new_settings.model_dump()
