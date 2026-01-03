"""
Role-Based Access Control (RBAC) Module

Defines roles, permissions, and access control logic.
"""

from enum import Enum
from functools import wraps
from typing import Callable

from pydantic import BaseModel


class Permission(str, Enum):
    """Available permissions in the system."""

    # Data Operations
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"

    # Validation Operations
    VALIDATE_RUN = "validate:run"
    VALIDATE_CONFIGURE = "validate:configure"

    # User Management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Workflow Operations
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_EXECUTE = "workflow:execute"

    # Audit Operations
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

    # Admin Operations
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_USERS = "admin:users"
    ADMIN_SECURITY = "admin:security"


class Role(str, Enum):
    """User roles with predefined permission sets."""

    VIEWER = "viewer"
    EDITOR = "editor"
    VALIDATOR = "validator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: {
        Permission.DATA_READ,
        Permission.AUDIT_READ,
    },
    Role.EDITOR: {
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_EXPORT,
        Permission.VALIDATE_RUN,
        Permission.AUDIT_READ,
    },
    Role.VALIDATOR: {
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_EXPORT,
        Permission.VALIDATE_RUN,
        Permission.VALIDATE_CONFIGURE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_EXECUTE,
        Permission.AUDIT_READ,
    },
    Role.ADMIN: {
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_DELETE,
        Permission.DATA_EXPORT,
        Permission.VALIDATE_RUN,
        Permission.VALIDATE_CONFIGURE,
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_WRITE,
        Permission.WORKFLOW_EXECUTE,
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        Permission.ADMIN_SETTINGS,
        Permission.ADMIN_USERS,
    },
    Role.SUPERADMIN: set(Permission),  # All permissions
}


class AccessContext(BaseModel):
    """Context for access control decisions."""
    user_id: str
    role: Role
    scopes: list[str] = []
    resource_owner: str | None = None


def get_role_permissions(role: Role) -> set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(
    role: Role,
    permission: Permission,
    scopes: list[str] | None = None,
) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role
        permission: Required permission
        scopes: Additional scopes from token (optional)

    Returns:
        True if permission is granted
    """
    # Check role-based permissions
    role_perms = get_role_permissions(role)
    if permission in role_perms:
        return True

    # Check scope-based permissions
    if scopes and permission.value in scopes:
        return True

    return False


def require_permission(permission: Permission) -> Callable:
    """
    Decorator to require a specific permission.

    Usage:
        @require_permission(Permission.DATA_WRITE)
        async def create_record(ctx: AccessContext, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Look for AccessContext in args or kwargs
            ctx = kwargs.get('ctx')
            if ctx is None:
                for arg in args:
                    if isinstance(arg, AccessContext):
                        ctx = arg
                        break

            if ctx is None:
                raise PermissionError("No access context provided")

            if not has_permission(ctx.role, permission, ctx.scopes):
                raise PermissionError(
                    f"Permission denied: {permission.value} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def can_access_resource(
    ctx: AccessContext,
    resource_owner_id: str,
    permission: Permission,
) -> bool:
    """
    Check if user can access a specific resource.

    Considers both role permissions and resource ownership.

    Args:
        ctx: Access context
        resource_owner_id: Owner of the resource
        permission: Required permission

    Returns:
        True if access is granted
    """
    # Superadmin can access everything
    if ctx.role == Role.SUPERADMIN:
        return True

    # Check if user owns the resource
    if ctx.user_id == resource_owner_id:
        return True

    # Check role-based permission
    return has_permission(ctx.role, permission, ctx.scopes)
