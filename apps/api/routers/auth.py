"""
Authentication router -- /api/v1/auth/*

POST /api/v1/auth/register    -- Create account
POST /api/v1/auth/login       -- Authenticate, issue tokens
POST /api/v1/auth/refresh     -- Rotate refresh token
POST /api/v1/auth/logout      -- Revoke tokens
GET  /api/v1/auth/me          -- Current user info
"""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    UserInfo,
)
from security.rbac import get_current_user
from services.auth_service import REFRESH_COOKIE_NAME, login_user, logout_user, refresh_token, register_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new applicant account",
)
def register(
    request_body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new user account.

    - Email must be unique
    - Password: min 8 chars, 1 uppercase, 1 lowercase, 1 digit
    - Account is immediately active (email verification planned for future phase)
    - Default role: applicant
    """
    return register_user(db, request_body)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and receive access token",
)
def login(
    request_body: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password.

    Returns a JWT access token (15 min) in the response body.
    Sets a refresh token (7 days) as an HTTP-only cookie.

    Account is locked for 15 minutes after 5 consecutive failed attempts.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return login_user(db, request_body, response, ip_address=ip, user_agent=ua)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Rotate refresh token and get new access token",
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """
    Exchange a valid refresh token for a new access token.

    The old refresh token is immediately revoked.
    A new refresh token is set in the HTTP-only cookie.
    """
    ip = request.client.host if request.client else None
    return refresh_token(db, response, refresh_cookie, ip_address=ip)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoke refresh token and clear session",
)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """
    Revoke the current refresh token and clear the session cookie.
    Access token remains valid until it expires (max 15 min).
    """
    return logout_user(db, response, refresh_cookie, current_user.id)


@router.get(
    "/me",
    response_model=UserInfo,
    summary="Get current authenticated user info",
)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's profile and assigned roles."""
    from models.user import UserRole, Role
    role_names = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == current_user.id)
        .all()
    )
    return UserInfo(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_email_verified=current_user.is_email_verified,
        roles=[r[0] for r in role_names],
    )
