"""
Security Configuration

Centralized security settings with secure defaults.
"""

import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    # JWT Settings
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # API Key Settings
    api_key_salt: str = secrets.token_urlsafe(16)
    api_key_prefix: str = "wk4_"

    # Encryption Settings
    encryption_key: str = secrets.token_urlsafe(32)  # 256-bit key

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Session Settings
    session_expire_hours: int = 24
    max_sessions_per_user: int = 5

    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    # Audit Settings
    audit_retention_days: int = 365
    audit_log_pii: bool = False  # Never log PII by default

    class Config:
        env_prefix = "WIKISOFT4_"
        env_file = ".env"


@lru_cache
def get_security_settings() -> SecuritySettings:
    """Get cached security settings."""
    return SecuritySettings()


# Global settings instance
security_settings = get_security_settings()
