"""
Authentication service  -  register, login, refresh, logout.

Security controls:
- bcrypt (cost 12) password hashing
- JWT access tokens (15 min)
- Refresh tokens stored as SHA-256 hash (7 days)
- Account lockout after 5 failed attempts (15 min)
- All auth events written to audit_logs
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from config import settings
from models.user import RefreshToken, Role, User, UserRole
from models.system import AuditLog
from schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, UserInfo
from security.auth import (
    create_access_token,
    create_refresh_token,
    get_expiry_datetime,
    hash_password,
    hash_refresh_token,
    verify_password,
)

# Account lockout config
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
REFRESH_COOKIE_NAME = "mota_refresh_token"


def _get_user_roles(db: Session, user_id: uuid.UUID) -> list[str]:
    roles = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return [r[0] for r in roles]


def _write_audit(db: Session, action: str, actor_id=None, resource_type="auth", details=None):
    db.add(AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        details=details or {},
    ))


def register_user(db: Session, request: RegisterRequest) -> RegisterResponse:
    """
    Register a new user account.

    - Validates email uniqueness
    - Hashes password (bcrypt cost 12)
    - Assigns 'applicant' role by default
    - Creates audit log entry
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Check phone uniqueness (if provided)
    if request.phone_number:
        existing_phone = db.query(User).filter(User.phone_number == request.phone_number).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

    # Get 'applicant' role
    applicant_role = db.query(Role).filter(Role.name == "applicant").first()
    if not applicant_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: 'applicant' role not found. Run seed_schemes.py.",
        )

    # Create user
    user = User(
        email=request.email.lower(),
        phone_number=request.phone_number,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        is_active=True,
        is_email_verified=False,  # Placeholder: email verification deferred to future phase
    )
    db.add(user)
    db.flush()  # Get user.id without committing

    # Assign applicant role
    db.add(UserRole(user_id=user.id, role_id=applicant_role.id))

    # Audit log
    _write_audit(db, "user.registered", actor_id=user.id, details={"email": user.email})

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        message="Registration successful. You can now log in.",
    )


def login_user(
    db: Session,
    request: LoginRequest,
    response: Response,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginResponse:
    """
    Authenticate a user and issue JWT access + refresh tokens.

    Security:
    - Constant-time password comparison (passlib)
    - Account lockout after MAX_FAILED_ATTEMPTS
    - Refresh token stored as SHA-256 hash in DB
    - Refresh token sent as HTTP-only, SameSite=Lax cookie
    """
    # Find user
    user = db.query(User).filter(User.email == request.email.lower()).first()

    # Generic error  -  don't reveal whether email exists
    invalid_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email address or password.",
    )

    if not user:
        raise invalid_creds

    # Check account lockout
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked. Please try again later.",
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            _write_audit(db, "user.account_locked", actor_id=user.id,
                         details={"failed_attempts": user.failed_login_count})
        _write_audit(db, "user.login_failed", actor_id=user.id, details={"ip": ip_address})
        raise invalid_creds

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")

    # Successful login  -  reset lockout state
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    # Get user roles
    role_names = _get_user_roles(db, user.id)

    # Create tokens
    access_token = create_access_token(subject=str(user.id), roles=role_names)
    raw_refresh, refresh_hash = create_refresh_token()

    # Store refresh token in DB
    expires = get_expiry_datetime(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires,
        user_agent=user_agent,
        ip_address=ip_address,
    ))

    # Set HTTP-only cookie
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        secure=settings.is_production,   # HTTPS only in production
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    _write_audit(db, "user.login_success", actor_id=user.id, details={"ip": ip_address})

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_email_verified=user.is_email_verified,
            roles=role_names,
        ),
    )


def refresh_token(
    db: Session,
    response: Response,
    raw_refresh_token: str | None,
    ip_address: str | None = None,
) -> dict:
    """
    Rotate refresh token.

    Old token is revoked. New token is issued.
    """
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token. Please log in again.",
    )

    if not raw_refresh_token:
        raise invalid

    token_hash = hash_refresh_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not stored or not stored.is_valid:
        raise invalid

    user = db.query(User).filter(User.id == stored.user_id, User.is_active == True).first()
    if not user:
        raise invalid

    # Revoke old token
    stored.revoked_at = datetime.now(timezone.utc)
    stored.revoked_reason = "rotated"

    # Issue new tokens
    role_names = _get_user_roles(db, user.id)
    access_token = create_access_token(subject=str(user.id), roles=role_names)
    raw_new, new_hash = create_refresh_token()

    expires = get_expiry_datetime(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=expires,
        ip_address=ip_address,
    ))

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_new,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    _write_audit(db, "user.token_refreshed", actor_id=user.id, details={"ip": ip_address})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def logout_user(
    db: Session,
    response: Response,
    raw_refresh_token: str | None,
    current_user_id: uuid.UUID,
) -> dict:
    """Revoke the refresh token and clear the cookie."""
    if raw_refresh_token:
        token_hash = hash_refresh_token(raw_refresh_token)
        stored = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user_id,
        ).first()
        if stored and not stored.is_revoked:
            stored.revoked_at = datetime.now(timezone.utc)
            stored.revoked_reason = "logout"

    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")
    _write_audit(db, "user.logout", actor_id=current_user_id)

    return {"message": "Logged out successfully."}
