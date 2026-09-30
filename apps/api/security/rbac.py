"""
FastAPI RBAC dependencies.

Usage:
    @router.get("/admin/thing")
    def admin_endpoint(current_user = Depends(require_roles(["super_admin"]))):
        ...
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from security.auth import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the authenticated user from the JWT access token.
    Used as a FastAPI dependency on protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception

    # Check if account is locked
    if user.locked_until:
        from datetime import datetime, timezone
        if datetime.now(timezone.utc) < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is temporarily locked due to too many failed login attempts.",
            )

    return user


get_current_active_user = get_current_user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None for unauthenticated requests."""
    if credentials is None:
        return None
    try:
        return get_current_user(credentials=credentials, db=db, request=None)
    except HTTPException:
        return None


def require_roles(allowed_roles: list[str]) -> Callable:
    """
    Dependency factory that enforces role-based access.

    Usage:
        Depends(require_roles(["scheme_admin", "super_admin"]))
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from models.user import UserRole, Role

        user_role_names = (
            db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == current_user.id)
            .all()
        )
        user_roles = {r[0] for r in user_role_names}

        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {allowed_roles}",
            )
        return current_user

    return dependency


def require_permissions(required_permissions: list[str]) -> Callable:
    """Dependency factory that enforces granular permission checks."""
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from models.user import UserRole, RolePermission, Permission
        perms = (
            db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .filter(UserRole.user_id == current_user.id)
            .all()
        )
        user_perms = {p[0] for p in perms}
        if not set(required_permissions).issubset(user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing permission(s): {required_permissions}",
            )
        return current_user
    return dependency


#  -  - - Pre-built role dependencies  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
require_applicant = require_roles(["applicant"])
require_officer = require_roles(["verification_officer", "scrutiny_officer", "selection_committee", "scheme_admin", "super_admin"])
require_scheme_admin = require_roles(["scheme_admin", "super_admin"])
require_super_admin = require_roles(["super_admin"])

