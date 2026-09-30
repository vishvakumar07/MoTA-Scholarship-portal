"""
JWT token creation, verification, and password hashing.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

#  -  - - Password hashing  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


#  -  - - Token creation  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
def create_access_token(
    subject: str,
    roles: list[str],
    additional_claims: dict | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID string)
        roles: List of role names
        additional_claims: Extra claims to embed
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": expires,
        "type": "access",
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """
    Create a cryptographically secure refresh token.

    Returns:
        (raw_token, token_hash)
        raw_token: sent to client (in HTTP-only cookie)
        token_hash: stored in database (SHA-256)
    """
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """Hash a raw refresh token for DB lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def hash_aadhaar(aadhaar_number: str) -> str:
    """
    One-way SHA-256 hash of an Aadhaar number.
    NEVER store raw Aadhaar numbers.
    """
    # Remove spaces/formatting
    clean = aadhaar_number.replace(" ", "").replace("-", "").strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


#  -  - - Token verification  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises:
        JWTError: If token is invalid, expired, or malformed
    """
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def get_expiry_datetime(days: int = 0, minutes: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days, minutes=minutes)
