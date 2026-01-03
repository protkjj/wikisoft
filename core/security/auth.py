"""
Authentication Module

Handles JWT tokens and API key authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import security_settings


class TokenData(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (user_id)
    exp: datetime
    iat: datetime
    scopes: list[str] = []


class User(BaseModel):
    """User model for authentication."""
    id: str
    email: str
    name: str
    role: str
    is_active: bool = True
    scopes: list[str] = []


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    user_id: str,
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: Unique user identifier
        scopes: Permission scopes for the token
        expires_delta: Token expiration time (default: 30 minutes)

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=30))

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "scopes": scopes or [],
    }

    return jwt.encode(
        payload,
        security_settings.jwt_secret_key,
        algorithm=security_settings.jwt_algorithm,
    )


def verify_token(token: str) -> TokenData | None:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            security_settings.jwt_secret_key,
            algorithms=[security_settings.jwt_algorithm],
        )
        return TokenData(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            scopes=payload.get("scopes", []),
        )
    except JWTError:
        return None


async def get_current_user(token: str) -> User | None:
    """
    Get current user from JWT token.

    This is a placeholder - in production, this would query the database.

    Args:
        token: JWT token string

    Returns:
        User if token is valid, None otherwise
    """
    token_data = verify_token(token)
    if token_data is None:
        return None

    # TODO: Query database for user
    # For now, return a placeholder
    return User(
        id=token_data.sub,
        email=f"{token_data.sub}@example.com",
        name="User",
        role="user",
        scopes=token_data.scopes,
    )


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        api_key: Plain text API key

    Returns:
        Hashed API key
    """
    return pwd_context.hash(api_key + security_settings.api_key_salt)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        plain_key: Plain text API key
        hashed_key: Stored hash

    Returns:
        True if key matches, False otherwise
    """
    return pwd_context.verify(plain_key + security_settings.api_key_salt, hashed_key)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
