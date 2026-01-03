"""
WIKISOFT 4.1 Core Security Module

Security by Design - All security features built-in from day one.

Components:
- auth: JWT authentication and API key management
- encryption: AES-256-GCM encryption for data at rest
- rbac: Role-Based Access Control
- audit: Action logging and audit trail
"""

from .auth import (
    create_access_token,
    verify_token,
    get_current_user,
    hash_api_key,
    verify_api_key,
)
from .encryption import (
    encrypt_data,
    decrypt_data,
    encrypt_field,
    decrypt_field,
)
from .rbac import (
    Permission,
    Role,
    has_permission,
    require_permission,
)
from .audit import (
    AuditAction,
    log_action,
    get_audit_trail,
)

__all__ = [
    # Auth
    "create_access_token",
    "verify_token",
    "get_current_user",
    "hash_api_key",
    "verify_api_key",
    # Encryption
    "encrypt_data",
    "decrypt_data",
    "encrypt_field",
    "decrypt_field",
    # RBAC
    "Permission",
    "Role",
    "has_permission",
    "require_permission",
    # Audit
    "AuditAction",
    "log_action",
    "get_audit_trail",
]
